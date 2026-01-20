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
        query = query.filter(SummaryUsage.date >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.date <= end_date)
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


def get_aggregated_records(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
) -> list[dict]:
    """文書別に集計した統計データを取得"""
    query = db.query(
        SummaryUsage.document_type,
        SummaryUsage.department,
        SummaryUsage.doctor,
        func.count(SummaryUsage.id).label("count"),
        func.sum(SummaryUsage.input_tokens).label("input_tokens"),
        func.sum(SummaryUsage.output_tokens).label("output_tokens"),
        func.sum(SummaryUsage.total_tokens).label("total_tokens"),
    )

    if start_date:
        query = query.filter(SummaryUsage.date >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.date <= end_date)
    if model:
        query = query.filter(SummaryUsage.model == model)
    if document_type:
        query = query.filter(SummaryUsage.document_type == document_type)

    results = (
        query.group_by(
            SummaryUsage.document_type, SummaryUsage.department, SummaryUsage.doctor
        )
        .order_by(SummaryUsage.document_type, SummaryUsage.department, SummaryUsage.doctor)
        .all()
    )

    return [
        {
            "document_type": r.document_type or "-",
            "department": r.department or "-",
            "doctor": r.doctor or "-",
            "count": r.count,
            "input_tokens": r.input_tokens or 0,
            "output_tokens": r.output_tokens or 0,
            "total_tokens": r.total_tokens or 0,
        }
        for r in results
    ]


def get_usage_records(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
    document_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SummaryUsage]:
    """使用統計レコードを取得（フィルター追加）"""
    query = db.query(SummaryUsage)

    if start_date:
        query = query.filter(SummaryUsage.date >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.date <= end_date)
    if model:
        query = query.filter(SummaryUsage.model == model)
    if document_type:
        query = query.filter(SummaryUsage.document_type == document_type)

    return query.order_by(SummaryUsage.date.desc()).offset(offset).limit(limit).all()
