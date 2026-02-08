import time
from typing import AsyncGenerator, cast

from app.core.config import get_settings
from app.core.constants import MESSAGES
from app.core.database import get_db_session
from app.external.gemini_api import GeminiAPIClient
from app.schemas.evaluation import EvaluationResponse
from app.services.evaluation_prompt_service import get_evaluation_prompt
from app.services.sse_helpers import sse_event, stream_with_heartbeat
from app.utils.exceptions import APIError

settings = get_settings()


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

    model_name = settings.gemini_evaluation_model
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
    if not output_summary:
        yield sse_event("error", {
            "success": False,
            "error_message": MESSAGES["VALIDATION"]["EVALUATION_NO_OUTPUT"]
        })
        return

    if not settings.gemini_evaluation_model:
        yield sse_event("error", {
            "success": False,
            "error_message": MESSAGES["CONFIG"]["EVALUATION_MODEL_MISSING"]
        })
        return

    with get_db_session() as db:
        prompt_data = get_evaluation_prompt(db, document_type)
        if not prompt_data:
            yield sse_event("error", {
                "success": False,
                "error_message": MESSAGES["VALIDATION"]["EVALUATION_PROMPT_NOT_SET"].format(
                    document_type=document_type
                )
            })
            return
        prompt_template = cast(str, prompt_data.content)

    start_time = time.time()

    async for item in stream_with_heartbeat(
        sync_func=_run_sync_evaluation,
        sync_func_args=(
            document_type, input_text, current_prescription,
            additional_info, output_summary, prompt_template
        ),
        start_message=MESSAGES["STATUS"]["EVALUATION_START"],
        running_status="evaluating",
        running_message=MESSAGES["STATUS"]["EVALUATING"],
        elapsed_message_template=MESSAGES["STATUS"]["EVALUATING_ELAPSED"],
    ):
        if isinstance(item, str):
            yield item
        else:
            # resultタプル
            evaluation_text, input_tokens, output_tokens = item
            processing_time = time.time() - start_time
            yield sse_event("complete", {
                "success": True,
                "evaluation_result": evaluation_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "processing_time": processing_time,
            })
