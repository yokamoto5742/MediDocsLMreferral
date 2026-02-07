import asyncio
import json
import logging
import time
from typing import AsyncGenerator, cast

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import MESSAGES
from app.core.database import get_db_session
from app.external.gemini_api import GeminiAPIClient
from app.models.evaluation_prompt import EvaluationPrompt
from app.schemas.evaluation import EvaluationResponse
from app.utils.exceptions import APIError

settings = get_settings()


def get_evaluation_prompt(db: Session, document_type: str) -> EvaluationPrompt | None:
    """評価プロンプトを取得"""
    return db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type,
        EvaluationPrompt.is_active == True
    ).first()


def get_all_evaluation_prompts(db: Session) -> list[EvaluationPrompt]:
    """全ての評価プロンプトを取得"""
    return db.query(EvaluationPrompt).order_by(EvaluationPrompt.document_type).all()


def create_or_update_evaluation_prompt(
    db: Session,
    document_type: str,
    content: str
) -> tuple[bool, str]:
    """評価プロンプトを作成または更新"""
    if not content:
        return False, MESSAGES["VALIDATION"]["EVALUATION_PROMPT_CONTENT_REQUIRED"]

    existing = db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type
    ).first()

    if existing:
        setattr(existing, 'content', content)
        setattr(existing, 'is_active', True)
        message = MESSAGES["SUCCESS"]["EVALUATION_PROMPT_UPDATED"]
    else:
        new_prompt = EvaluationPrompt(
            document_type=document_type,
            content=content,
            is_active=True
        )
        db.add(new_prompt)
        message = MESSAGES["SUCCESS"]["EVALUATION_PROMPT_CREATED"]

    return True, message


def delete_evaluation_prompt(db: Session, document_type: str) -> tuple[bool, str]:
    """評価プロンプトを削除"""
    prompt = db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type
    ).first()

    if not prompt:
        return False, MESSAGES["ERROR"]["EVALUATION_PROMPT_NOT_FOUND"].format(
            document_type=document_type
        )

    db.delete(prompt)
    return True, MESSAGES["SUCCESS"]["EVALUATION_PROMPT_DELETED"]


def build_evaluation_prompt(
    prompt_template: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str
) -> str:
    return f"""{prompt_template}

【カルテ記載】
{input_text}

【現在の処方】
{current_prescription}

【追加情報】
{additional_info}

【生成された出力】
{output_summary}
"""


def execute_evaluation(
    document_type: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str
) -> EvaluationResponse:
    """出力評価を実行"""
    if not output_summary:
        return EvaluationResponse(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=0.0,
            error_message=MESSAGES["VALIDATION"]["EVALUATION_NO_OUTPUT"]
        )

    if not settings.gemini_evaluation_model:
        return EvaluationResponse(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=0.0,
            error_message=MESSAGES["CONFIG"]["EVALUATION_MODEL_MISSING"]
        )

    with get_db_session() as db:
        prompt_data = get_evaluation_prompt(db, document_type)
        if not prompt_data:
            return EvaluationResponse(
                success=False,
                evaluation_result="",
                input_tokens=0,
                output_tokens=0,
                processing_time=0.0,
                error_message=MESSAGES["VALIDATION"]["EVALUATION_PROMPT_NOT_SET"].format(
                    document_type=document_type
                )
            )
        prompt_template = cast(str, prompt_data.content)

    full_prompt = build_evaluation_prompt(
        prompt_template,
        input_text,
        current_prescription,
        additional_info,
        output_summary
    )

    start_time = time.time()
    try:
        client = GeminiAPIClient(model_name=settings.gemini_evaluation_model)
        client.initialize()

        evaluation_text, input_tokens, output_tokens = client._generate_content(
            full_prompt, settings.gemini_evaluation_model
        )
        processing_time = time.time() - start_time

        return EvaluationResponse(
            success=True,
            evaluation_result=evaluation_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time=processing_time
        )

    except APIError as e:
        return EvaluationResponse(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=time.time() - start_time,
            error_message=str(e)
        )
    except Exception as e:
        return EvaluationResponse(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=time.time() - start_time,
            error_message=MESSAGES["ERROR"]["EVALUATION_API_ERROR"].format(error=str(e))
        )


def _sse_event(event_type: str, data: dict) -> str:
    """SSEイベント文字列を生成"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_sync_evaluation(
    document_type: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str,
    prompt_template: str
) -> tuple[str, int, int]:
    """同期的に評価を実行"""
    full_prompt = build_evaluation_prompt(
        prompt_template,
        input_text,
        current_prescription,
        additional_info,
        output_summary
    )

    model_name = cast(str, settings.gemini_evaluation_model)
    client = GeminiAPIClient(model_name=model_name)
    client.initialize()

    evaluation_text, input_tokens, output_tokens = client._generate_content(
        full_prompt, model_name
    )

    return evaluation_text, input_tokens, output_tokens


async def execute_evaluation_stream(
    document_type: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str
) -> AsyncGenerator[str, None]:
    """SSEストリーミングで評価を実行"""
    # 入力検証
    if not output_summary:
        yield _sse_event("error", {
            "success": False,
            "error_message": MESSAGES["VALIDATION"]["EVALUATION_NO_OUTPUT"]
        })
        return

    if not settings.gemini_evaluation_model:
        yield _sse_event("error", {
            "success": False,
            "error_message": MESSAGES["CONFIG"]["EVALUATION_MODEL_MISSING"]
        })
        return

    # プロンプト取得
    with get_db_session() as db:
        prompt_data = get_evaluation_prompt(db, document_type)
        if not prompt_data:
            yield _sse_event("error", {
                "success": False,
                "error_message": MESSAGES["VALIDATION"]["EVALUATION_PROMPT_NOT_SET"].format(
                    document_type=document_type
                )
            })
            return
        prompt_template = cast(str, prompt_data.content)

    # 評価開始を通知
    yield _sse_event("progress", {
        "status": "starting",
        "message": MESSAGES["STATUS"]["EVALUATION_START"]
    })

    start_time = time.time()
    queue: asyncio.Queue = asyncio.Queue()

    async def _evaluation_task():
        """評価をスレッドで実行し結果をキューに入れる"""
        try:
            result = await asyncio.to_thread(
                _run_sync_evaluation,
                document_type, input_text, current_prescription,
                additional_info, output_summary, prompt_template
            )
            await queue.put(("result", result))
        except Exception as e:
            logging.error(f"Evaluation task error: {e}", exc_info=True)
            await queue.put(("error", str(e)))

    # 評価タスクを開始
    task = asyncio.create_task(_evaluation_task())

    # 評価開始を再度通知
    yield _sse_event("progress", {
        "status": "evaluating",
        "message": MESSAGES["STATUS"]["EVALUATING"]
    })

    # ハートビートを送信しながら結果を待つ
    HEARTBEAT_INTERVAL = 5
    evaluation_text = ""
    input_tokens = 0
    output_tokens = 0

    while not task.done():
        try:
            # キューから結果を取得
            msg_type, msg_data = await asyncio.wait_for(
                queue.get(), timeout=HEARTBEAT_INTERVAL
            )
            if msg_type == "error":
                yield _sse_event("error", {
                    "success": False,
                    "error_message": MESSAGES["ERROR"]["EVALUATION_API_ERROR"].format(error=msg_data)
                })
                return
            # msg_type == "result"
            evaluation_text, input_tokens, output_tokens = msg_data
            break
        except asyncio.TimeoutError:
            # ハートビートを送信
            elapsed = int(time.time() - start_time)
            yield _sse_event("progress", {
                "status": "evaluating",
                "message": MESSAGES["STATUS"]["EVALUATING_ELAPSED"].format(
                    elapsed=elapsed
                )
            })

    processing_time = time.time() - start_time

    # 完了イベント
    yield _sse_event("complete", {
        "success": True,
        "evaluation_result": evaluation_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "processing_time": processing_time,
    })
