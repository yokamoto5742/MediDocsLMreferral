import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.database import get_db_session
from app.external.api_factory import generate_summary
from app.models.usage import SummaryUsage
from app.schemas.summary import SummaryResponse
from app.utils.text_processor import format_output_summary, parse_output_summary

JST = ZoneInfo("Asia/Tokyo")
settings = get_settings()


def validate_input(medical_text: str) -> tuple[bool, str | None]:
    """入力検証"""
    if not medical_text or not medical_text.strip():
        return False, "カルテ情報を入力してください"

    input_length = len(medical_text.strip())
    if input_length < settings.min_input_tokens:
        return False, "入力文字数が少なすぎます"
    if input_length > settings.max_input_tokens:
        return False, f"入力文字数が{settings.max_input_tokens}を超えています"

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
    # プロンプトからモデルを取得
    if not model_explicitly_selected:
        try:
            from app.core.database import get_db_session
            from app.services import prompt_service

            with get_db_session() as db:
                prompt_data = prompt_service.get_prompt(db, department, document_type, doctor)
                if prompt_data:
                    selected = prompt_data.selected_model
                    if selected is not None:
                        requested_model = str(selected)
        except Exception:
            # プロンプト取得に失敗しても処理を続行
            pass

    # 入力長による自動切替
    if input_length > settings.max_token_threshold and requested_model == "Claude":
        if settings.gemini_model:
            return "Gemini_Pro", True
        else:
            # Geminiが利用できない場合はエラー
            raise ValueError("入力が長すぎますが、Geminiモデルが設定されていません")

    return requested_model, False


def get_provider_and_model(selected_model: str) -> tuple[str, str]:
    """モデル名からプロバイダーとモデル名を取得"""
    if selected_model == "Claude":
        model = settings.claude_model or settings.anthropic_model
        if not model:
            raise ValueError("Claudeモデルが設定されていません")
        return "claude", model
    elif selected_model == "Gemini_Pro":
        model = settings.gemini_model
        if not model:
            raise ValueError("Geminiモデルが設定されていません")
        return "gemini", model
    else:
        raise ValueError(f"サポートされていないモデル: {selected_model}")


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
        return SummaryResponse(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=model,
            model_switched=False,
            error_message=error_msg,
        )

    # モデル決定
    total_length = len(medical_text) + len(additional_info or "")
    try:
        final_model, model_switched = determine_model(
            model, total_length, department, document_type, doctor, model_explicitly_selected
        )
    except ValueError as e:
        return SummaryResponse(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=model,
            model_switched=False,
            error_message=str(e),
        )

    # プロバイダーとモデル名を取得
    try:
        provider, model_name = get_provider_and_model(final_model)
    except ValueError as e:
        return SummaryResponse(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=final_model,
            model_switched=model_switched,
            error_message=str(e),
        )

    # AI API 呼び出し
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
        return SummaryResponse(
            success=False,
            output_summary="",
            parsed_summary={},
            input_tokens=0,
            output_tokens=0,
            processing_time=0,
            model_used=final_model,
            model_switched=model_switched,
            error_message=str(e),
        )

    processing_time = time.time() - start_time

    # 出力フォーマット
    formatted_summary = format_output_summary(output_summary)
    parsed_summary = parse_output_summary(formatted_summary)

    # 使用統計保存
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
    """使用統計をDBに保存"""
    import logging

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
        # ログに記録するが、エラーは無視（統計保存失敗で処理全体を失敗させない）
        logging.error(f"Failed to save usage statistics: {e}", exc_info=True)
