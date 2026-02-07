from fastapi import APIRouter

from app.core.constants import DEFAULT_DEPARTMENT, DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/departments")
def get_departments():
    """診療科一覧を取得"""
    return {"departments": DEFAULT_DEPARTMENT}


@router.get("/doctors/{department}")
def get_doctors(department: str):
    """診療科の医師一覧を取得"""
    doctors = DEPARTMENT_DOCTORS_MAPPING.get(department, ["default"])
    return {"doctors": doctors}


@router.get("/document-types")
def get_document_types():
    """文書タイプ一覧を取得"""
    return {"document_types": DOCUMENT_TYPES}
