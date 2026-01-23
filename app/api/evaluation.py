from datetime import datetime
from typing import cast

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

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_output(request: EvaluationRequest):
    """出力評価API"""
    result = evaluation_service.execute_evaluation(
        document_type=request.document_type,
        input_text=request.input_text,
        current_prescription=request.current_prescription,
        additional_info=request.additional_info,
        output_summary=request.output_summary,
    )
    return EvaluationResponse(
        success=result.success,
        evaluation_result=result.evaluation_result,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        processing_time=result.processing_time,
        error_message=result.error_message,
    )


@router.get("/prompts", response_model=EvaluationPromptListResponse)
def get_all_evaluation_prompts(db: Session = Depends(get_db)):
    """全ての評価プロンプトを取得"""
    prompts = evaluation_service.get_all_evaluation_prompts(db)
    return EvaluationPromptListResponse(
        prompts=[
            EvaluationPromptResponse(
                id=cast(int, p.id),
                document_type=cast(str, p.document_type),
                content=cast(str, p.content),
                is_active=cast(bool, p.is_active),
                created_at=cast(datetime | None, p.created_at),
                updated_at=cast(datetime | None, p.updated_at),
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
            id=cast(int, prompt.id),
            document_type=cast(str, prompt.document_type),
            content=cast(str, prompt.content),
            is_active=cast(bool, prompt.is_active),
            created_at=cast(datetime | None, prompt.created_at),
            updated_at=cast(datetime | None, prompt.updated_at),
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
