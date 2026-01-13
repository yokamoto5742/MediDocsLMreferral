from fastapi import APIRouter

from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import execute_summary_generation
from app.core.config import get_settings

router = APIRouter(prefix="/summary", tags=["summary"])
settings = get_settings()


@router.post("/generate", response_model=SummaryResponse)
def generate_summary(request: SummaryRequest):
    """文書生成API"""
    result = execute_summary_generation(
        medical_text=request.medical_text,
        additional_info=request.additional_info,
        referral_purpose=request.referral_purpose,
        current_prescription=request.current_prescription,
        department=request.department,
        doctor=request.doctor,
        document_type=request.document_type,
        model=request.model,
        model_explicitly_selected=request.model_explicitly_selected,
    )
    return SummaryResponse(
        success=result.success,
        output_summary=result.output_summary,
        parsed_summary=result.parsed_summary,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        processing_time=result.processing_time,
        model_used=result.model_used,
        model_switched=result.model_switched,
        error_message=result.error_message,
    )


@router.get("/models")
def get_available_models():
    """利用可能なモデル一覧を取得"""
    models = []
    if settings.anthropic_model or settings.claude_api_key:
        models.append("Claude")
    if settings.gemini_model:
        models.append("Gemini_Pro")
    return {
        "available_models": models,
        "default_model": models[0] if models else None,
    }
