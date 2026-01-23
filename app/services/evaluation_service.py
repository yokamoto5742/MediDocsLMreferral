import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import MESSAGES
from app.core.database import get_db_session
from app.external.gemini_evaluation import GeminiEvaluationClient
from app.models.evaluation_prompt import EvaluationPrompt
from app.utils.exceptions import APIError

settings = get_settings()


@dataclass
class EvaluationResult:
    success: bool
    evaluation_result: str
    input_tokens: int
    output_tokens: int
    processing_time: float
    error_message: str | None = None


def get_evaluation_prompt(db: Session, document_type: str) -> EvaluationPrompt | None:
    """評価プロンプトを取得"""
    return db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type,
        EvaluationPrompt.is_active == True  # noqa: E712
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
        return False, "評価プロンプトの内容を入力してください"

    existing = db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type
    ).first()

    if existing:
        existing.content = content
        existing.is_active = True
        message = MESSAGES["EVALUATION_PROMPT_UPDATED"]
    else:
        new_prompt = EvaluationPrompt(
            document_type=document_type,
            content=content,
            is_active=True
        )
        db.add(new_prompt)
        message = MESSAGES["EVALUATION_PROMPT_CREATED"]

    return True, message


def delete_evaluation_prompt(db: Session, document_type: str) -> tuple[bool, str]:
    """評価プロンプトを削除"""
    prompt = db.query(EvaluationPrompt).filter(
        EvaluationPrompt.document_type == document_type
    ).first()

    if not prompt:
        return False, f"{document_type}の評価プロンプトが見つかりません"

    db.delete(prompt)
    return True, MESSAGES["EVALUATION_PROMPT_DELETED"]


def build_evaluation_prompt(
    prompt_template: str,
    input_text: str,
    current_prescription: str,
    additional_info: str,
    output_summary: str
) -> str:
    """評価用のフルプロンプトを構築"""
    return f"""{prompt_template}

【カルテ記載】
{input_text}

【退院時処方(現在の処方)】
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
) -> EvaluationResult:
    """出力評価を実行"""
    # 評価対象の検証
    if not output_summary:
        return EvaluationResult(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            error_message=MESSAGES["EVALUATION_NO_OUTPUT"]
        )

    # 評価モデルの検証
    if not settings.gemini_evaluation_model:
        return EvaluationResult(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            error_message=MESSAGES["EVALUATION_MODEL_MISSING"]
        )

    # 評価プロンプトの取得
    with get_db_session() as db:
        prompt_data = get_evaluation_prompt(db, document_type)
        if not prompt_data:
            return EvaluationResult(
                success=False,
                evaluation_result="",
                input_tokens=0,
                output_tokens=0,
                processing_time=0,
                error_message=MESSAGES["EVALUATION_PROMPT_NOT_SET"].format(
                    document_type=document_type
                )
            )
        prompt_template = prompt_data.content

    # フルプロンプト構築
    full_prompt = build_evaluation_prompt(
        prompt_template,
        input_text,
        current_prescription,
        additional_info,
        output_summary
    )

    # 評価実行
    start_time = time.time()
    try:
        client = GeminiEvaluationClient()
        client.initialize()

        evaluation_text, input_tokens, output_tokens = client._generate_content(
            full_prompt, settings.gemini_evaluation_model
        )
        processing_time = time.time() - start_time

        return EvaluationResult(
            success=True,
            evaluation_result=evaluation_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            processing_time=processing_time
        )

    except APIError as e:
        return EvaluationResult(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=time.time() - start_time,
            error_message=str(e)
        )
    except Exception as e:
        return EvaluationResult(
            success=False,
            evaluation_result="",
            input_tokens=0,
            output_tokens=0,
            processing_time=time.time() - start_time,
            error_message=MESSAGES["EVALUATION_API_ERROR"].format(error=str(e))
        )
