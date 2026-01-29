from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt


def get_all_prompts(db: Session) -> list[Prompt]:
    """全プロンプトを取得（更新日時降順）"""
    query = select(Prompt).order_by(Prompt.updated_at.desc())
    return list(db.execute(query).scalars().all())


def get_prompt(
    db: Session,
    department: str,
    document_type: str,
    doctor: str,
) -> Prompt | None:
    """特定のプロンプトを取得"""
    return (
        db.query(Prompt)
        .filter(
            Prompt.department == department,
            Prompt.document_type == document_type,
            Prompt.doctor == doctor,
        )
        .first()
    )


def get_prompt_by_id(db: Session, prompt_id: int) -> Prompt | None:
    """IDでプロンプトを取得"""
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


def get_selected_model(
    db: Session,
    department: str,
    document_type: str,
    doctor: str
) -> str | None:
    """プロンプトから選択されたモデル名を取得"""
    prompt = get_prompt(db, department, document_type, doctor)
    if prompt and prompt.selected_model:
        return str(prompt.selected_model)
    return None


def create_or_update_prompt(
    db: Session,
    department: str,
    document_type: str,
    doctor: str,
    content: str,
    selected_model: str | None = None,
) -> Prompt:
    """プロンプトを作成または更新"""
    existing = get_prompt(db, department, document_type, doctor)
    if existing:
        existing.content = content
        existing.selected_model = selected_model
        return existing

    new_prompt = Prompt(
        department=department,
        document_type=document_type,
        doctor=doctor,
        content=content,
        selected_model=selected_model,
    )
    db.add(new_prompt)
    return new_prompt


def delete_prompt(db: Session, prompt_id: int) -> bool:
    """プロンプトを削除"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        db.delete(prompt)
        return True
    return False
