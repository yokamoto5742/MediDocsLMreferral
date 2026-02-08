import logging
import time
from datetime import datetime
from typing import AsyncGenerator
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.constants import MESSAGES, ModelType
from app.core.database import get_db_session
from app.external.api_factory import APIProvider, generate_summary, generate_summary_stream
from app.models.usage import SummaryUsage
from app.schemas.summary import SummaryResponse
from app.services.sse_helpers import sse_event, stream_with_heartbeat
from app.utils.text_processor import format_output_summary, parse_output_summary

JST = ZoneInfo("Asia/Tokyo")
settings = get_settings()


def _error_response(
        error_msg: str,
        model: str,
        model_switched: bool = False
) -> SummaryResponse:
    return SummaryResponse(
        success=False,
        output_summary="",
        parsed_summary={},
        input_tokens=0,
        output_tokens=0,
        processing_time=0,
        model_used=model,
        model_switched=model_switched,
        error_message=error_msg,
    )


def validate_input(medical_text: str) -> tuple[bool, str | None]:
    """入力検証"""
    if not medical_text or not medical_text.strip():
        return False, MESSAGES["VALIDATION"]["NO_INPUT"]

    input_length = len(medical_text.strip())
    if input_length < settings.min_input_tokens:
        return False, MESSAGES["VALIDATION"]["INPUT_TOO_SHORT"]
    if input_length > settings.max_input_tokens:
        return False, MESSAGES["VALIDATION"]["INPUT_TOO_LONG"]

    return True, None


def determine_model(
    requested_model: str,
    input_length: int,
    department: str,
    document_type: str,
    doctor: str,
    model_explicitly_selected: bool = False
) -> tuple[str, bool]:
    """モデル自動切替判定"""
    if not model_explicitly_selected:
        try:
            from app.services.prompt_service import get_selected_model

            with get_db_session() as db:
                selected = get_selected_model(db, department, document_type, doctor)
                if selected is not None:
                    requested_model = selected
        except Exception:
            # プロンプト取得に失敗しても処理を続行
            pass

    # 入力長による自動切替
    if input_length > settings.max_token_threshold and requested_model == ModelType.CLAUDE:
        if settings.gemini_model:
            return ModelType.GEMINI_PRO, True
        else:
            raise ValueError(MESSAGES["CONFIG"]["THRESHOLD_EXCEEDED_NO_GEMINI"])

    return requested_model, False


def get_provider_and_model(selected_model: str) -> tuple[str, str]:
    """モデル名からプロバイダーとモデル名を取得"""
    if selected_model == ModelType.CLAUDE:
        model = settings.claude_model or settings.anthropic_model
        if not model:
            raise ValueError(MESSAGES["CONFIG"]["CLAUDE_MODEL_NOT_SET"])
        return APIProvider.CLAUDE.value, model
    elif selected_model == ModelType.GEMINI_PRO:
        model = settings.gemini_model
        if not model:
            raise ValueError(MESSAGES["CONFIG"]["GEMINI_MODEL_NOT_SET"])
        return APIProvider.GEMINI.value, model
    else:
        raise ValueError(
            MESSAGES["CONFIG"]["UNSUPPORTED_MODEL"].format(model=selected_model)
        )


def execute_summary_generation(
    medical_text: str,
    additional_info: str,
    referral_purpose: str,
    current_prescription: str,
    department: str,
    doctor: str,
    document_type: str,
    model: str,
    model_explicitly_selected: bool = False,
) -> SummaryResponse:
    """文書生成を実行"""
    # 入力検証
    is_valid, error_msg = validate_input(medical_text)
    if not is_valid:
        return _error_response(error_msg or MESSAGES["ERROR"]["INPUT_ERROR"], model)

    # モデル決定
    total_length = len(medical_text) + len(additional_info or "")
    try:
        final_model, model_switched = determine_model(
            model, total_length, department, document_type, doctor, model_explicitly_selected
        )
    except ValueError as e:
        return _error_response(str(e), model)

    # プロバイダーとモデル名を取得
    try:
        provider, model_name = get_provider_and_model(final_model)
    except ValueError as e:
        return _error_response(str(e), final_model, model_switched)

    start_time = time.time()
    try:
        output_summary, input_tokens, output_tokens = generate_summary(
            provider=provider,
            medical_text=medical_text,
            additional_info=additional_info,
            referral_purpose=referral_purpose,
            current_prescription=current_prescription,
            department=department,
            document_type=document_type,
            doctor=doctor,
            model_name=model_name,
        )
    except Exception as e:
        return _error_response(str(e), final_model, model_switched)

    processing_time = time.time() - start_time

    formatted_summary = format_output_summary(output_summary)
    parsed_summary = parse_output_summary(formatted_summary)

    save_usage(
        department=department,
        doctor=doctor,
        document_type=document_type,
        model=final_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        processing_time=processing_time,
    )

    return SummaryResponse(
        success=True,
        output_summary=formatted_summary,
        parsed_summary=parsed_summary,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        processing_time=processing_time,
        model_used=final_model,
        model_switched=model_switched,
    )


def save_usage(
    department: str,
    doctor: str,
    document_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    processing_time: float,
) -> None:
    """使用統計を保存"""

    try:
        with get_db_session() as db:
            usage = SummaryUsage(
                date=datetime.now(JST),
                department=department,
                doctor=doctor,
                document_type=document_type,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                app_type="referral_letter",
                processing_time=processing_time,
            )
            db.add(usage)
    except Exception as e:
        # ログに記録するがエラーは無視
        logging.error(f"Failed to save usage statistics: {e}", exc_info=True)


def _run_sync_generation(
    provider: str,
    medical_text: str,
    additional_info: str,
    referral_purpose: str,
    current_prescription: str,
    department: str,
    document_type: str,
    doctor: str,
    model_name: str,
) -> tuple[str, int, int]:
    """同期ストリーミングジェネレータをスレッドプールで実行"""
    stream = generate_summary_stream(
        provider=provider,
        medical_text=medical_text,
        additional_info=additional_info,
        referral_purpose=referral_purpose,
        current_prescription=current_prescription,
        department=department,
        document_type=document_type,
        doctor=doctor,
        model_name=model_name,
    )
    chunks = []
    metadata = {}
    for item in stream:
        if isinstance(item, dict):
            metadata = item
        else:
            chunks.append(item)
    return "".join(chunks), metadata.get("input_tokens", 0), metadata.get("output_tokens", 0)


async def execute_summary_generation_stream(
    medical_text: str,
    additional_info: str,
    referral_purpose: str,
    current_prescription: str,
    department: str,
    doctor: str,
    document_type: str,
    model: str,
    model_explicitly_selected: bool = False,
) -> AsyncGenerator[str, None]:
    """SSEストリーミングで文書生成を実行"""
    # 入力検証
    is_valid, error_msg = validate_input(medical_text)
    if not is_valid:
        yield sse_event("error", {
            "success": False,
            "error_message": error_msg or MESSAGES["ERROR"]["INPUT_ERROR"]
        })
        return

    # モデル決定
    total_length = len(medical_text) + len(additional_info or "")
    try:
        final_model, model_switched = determine_model(
            model, total_length, department, document_type,
            doctor, model_explicitly_selected
        )
    except ValueError as e:
        yield sse_event("error", {"success": False, "error_message": str(e)})
        return

    # プロバイダーとモデル名を取得
    try:
        provider, model_name = get_provider_and_model(final_model)
    except ValueError as e:
        yield sse_event("error", {"success": False, "error_message": str(e)})
        return

    start_time = time.time()

    async for item in stream_with_heartbeat(
        sync_func=_run_sync_generation,
        sync_func_args=(
            provider, medical_text, additional_info, referral_purpose,
            current_prescription, department, document_type, doctor, model_name
        ),
        start_message=MESSAGES["STATUS"]["DOCUMENT_GENERATION_START"],
        running_status="generating",
        running_message=MESSAGES["STATUS"]["DOCUMENT_GENERATING"],
        elapsed_message_template=MESSAGES["STATUS"]["DOCUMENT_GENERATING_ELAPSED"],
    ):
        if isinstance(item, str):
            yield item
        else:
            # resultタプル
            full_text, input_tokens, output_tokens = item
            processing_time = time.time() - start_time

            formatted_summary = format_output_summary(full_text)
            parsed_summary = parse_output_summary(formatted_summary)

            save_usage(
                department=department, doctor=doctor, document_type=document_type,
                model=final_model, input_tokens=input_tokens,
                output_tokens=output_tokens, processing_time=processing_time,
            )

            yield sse_event("complete", {
                "success": True,
                "output_summary": formatted_summary,
                "parsed_summary": parsed_summary,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "processing_time": processing_time,
                "model_used": final_model,
                "model_switched": model_switched,
            })
