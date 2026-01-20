from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse
from app.services import prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/", response_model=list[PromptResponse])
def list_prompts(db: Session = Depends(get_db)):
    """プロンプト一覧を取得"""
    return prompt_service.get_all_prompts(db)


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """単一プロンプトを取得"""
    prompt = prompt_service.get_prompt_by_id(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    """プロンプトを作成または更新"""
    result = prompt_service.create_or_update_prompt(
        db,
        department=prompt.department,
        document_type=prompt.document_type,
        doctor=prompt.doctor,
        content=prompt.content,
        selected_model=prompt.selected_model,
    )
    db.commit()
    db.refresh(result)
    return result


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """プロンプトを削除"""
    if not prompt_service.delete_prompt(db, prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.commit()
    return {"status": "deleted"}
