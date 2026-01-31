from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.evaluation import (
    EvaluationPromptListResponse,
    EvaluationPromptRequest,
    EvaluationPromptResponse,
    EvaluationPromptSaveResponse,
    EvaluationRequest,
    EvaluationResponse,
)
from app.services import evaluation_service

# 管理用ルーター（認証不要）
router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# 公開APIルーター（認証必須）
protected_router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@protected_router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_output(request: EvaluationRequest):
    """出力評価API（認証必須）"""
    return evaluation_service.execute_evaluation(
        document_type=request.document_type,
        input_text=request.input_text,
        current_prescription=request.current_prescription,
        additional_info=request.additional_info,
        output_summary=request.output_summary,
    )


@router.get("/prompts", response_model=EvaluationPromptListResponse)
def get_all_evaluation_prompts(db: Session = Depends(get_db)):
    """全ての評価プロンプトを取得"""
    prompts = evaluation_service.get_all_evaluation_prompts(db)
    return EvaluationPromptListResponse(
        prompts=[
            EvaluationPromptResponse(
                id=p.id,  # type: ignore[assignment]
                document_type=p.document_type,  # type: ignore[assignment]
                content=p.content,  # type: ignore[assignment]
                is_active=p.is_active,  # type: ignore[assignment]
                created_at=p.created_at,  # type: ignore[assignment]
                updated_at=p.updated_at,  # type: ignore[assignment]
            )
            for p in prompts
        ]
    )


@router.get("/prompts/{document_type}", response_model=EvaluationPromptResponse)
def get_evaluation_prompt(
    document_type: str,
    db: Session = Depends(get_db)
):
    """評価プロンプトを取得"""
    prompt = evaluation_service.get_evaluation_prompt(db, document_type)
    if prompt:
        return EvaluationPromptResponse(
            id=prompt.id,  # type: ignore[assignment]
            document_type=prompt.document_type,  # type: ignore[assignment]
            content=prompt.content,  # type: ignore[assignment]
            is_active=prompt.is_active,  # type: ignore[assignment]
            created_at=prompt.created_at,  # type: ignore[assignment]
            updated_at=prompt.updated_at,  # type: ignore[assignment]
        )
    return EvaluationPromptResponse(
        document_type=document_type,
        content=None,
        is_active=False,
    )


@router.post("/prompts", response_model=EvaluationPromptSaveResponse)
def save_evaluation_prompt(
    request: EvaluationPromptRequest,
    db: Session = Depends(get_db)
):
    """評価プロンプトを保存"""
    success, message = evaluation_service.create_or_update_evaluation_prompt(
        db, request.document_type, request.content
    )
    if success:
        db.commit()
    return EvaluationPromptSaveResponse(
        success=success,
        message=message,
        document_type=request.document_type,
    )


@router.delete("/prompts/{document_type}", response_model=EvaluationPromptSaveResponse)
def delete_evaluation_prompt(
    document_type: str,
    db: Session = Depends(get_db)
):
    """評価プロンプトを削除"""
    success, message = evaluation_service.delete_evaluation_prompt(db, document_type)
    if success:
        db.commit()
    return EvaluationPromptSaveResponse(
        success=success,
        message=message,
        document_type=document_type,
    )
