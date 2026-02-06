from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.constants import ModelType
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import execute_summary_generation, execute_summary_generation_stream

# 管理用ルーター（認証不要）（Web UIから使用）
router = APIRouter(prefix="/summary", tags=["summary"])

# 公開APIルーター（認証必須）
protected_router = APIRouter(prefix="/summary", tags=["summary"])

settings = get_settings()


@protected_router.post("/generate", response_model=SummaryResponse)
def generate_summary(request: SummaryRequest):
    """文書生成API（CSRF認証必須）"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"通常文書生成開始: model={request.model}, dept={request.department}")

    return execute_summary_generation(
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


@protected_router.post("/generate-stream")
async def generate_summary_stream(request: SummaryRequest):
    """SSEストリーミング文書生成API（CSRF認証必須）"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"SSEストリーミング文書生成開始: model={request.model}, dept={request.department}")

    event_generator = execute_summary_generation_stream(
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
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models")
def get_available_models():
    """利用可能なモデル一覧を取得"""
    models = []
    if settings.anthropic_model or settings.claude_api_key:
        models.append(ModelType.CLAUDE.value)
    if settings.gemini_model:
        models.append(ModelType.GEMINI_PRO.value)
    return {
        "available_models": models,
        "default_model": models[0] if models else None,
    }
