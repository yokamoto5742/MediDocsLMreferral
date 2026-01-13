from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.usage import SummaryUsage


def get_usage_summary(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
) -> dict:
    """使用統計サマリーを取得"""
    query = db.query(SummaryUsage)

    if start_date:
        query = query.filter(SummaryUsage.created_at >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.created_at <= end_date)
    if model:
        query = query.filter(SummaryUsage.model == model)

    total_count = query.count()
    total_input = query.with_entities(func.sum(SummaryUsage.input_tokens)).scalar() or 0
    total_output = query.with_entities(func.sum(SummaryUsage.output_tokens)).scalar() or 0
    avg_time = query.with_entities(func.avg(SummaryUsage.processing_time)).scalar() or 0

    return {
        "total_count": total_count,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "average_processing_time": round(avg_time, 2),
    }


def get_usage_records(
    db: Session,
    limit: int = 100,
    offset: int = 0,
) -> list[SummaryUsage]:
    """使用統計レコードを取得"""
    return (
        db.query(SummaryUsage)
        .order_by(SummaryUsage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
