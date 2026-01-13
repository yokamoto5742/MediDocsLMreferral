from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.statistics import UsageSummary, UsageRecord
from app.services import statistics_service

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/summary", response_model=UsageSummary)
def get_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    db: Session = Depends(get_db),
):
    """使用統計サマリーを取得"""
    return statistics_service.get_usage_summary(db, start_date, end_date, model)


@router.get("/records", response_model=list[UsageRecord])
def get_records(
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """使用統計レコードを取得"""
    return statistics_service.get_usage_records(db, limit, offset)
