from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.models.usage import SummaryUsage


def get_usage_summary(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    model: str | None = None,
) -> dict:
    """使用統計サマリーを取得"""
    query = db.query(
        func.count(SummaryUsage.id),
        func.sum(SummaryUsage.input_tokens),
        func.sum(SummaryUsage.output_tokens),
        func.avg(SummaryUsage.processing_time),
    )

    if start_date:
        query = query.filter(SummaryUsage.date >= start_date)
    if end_date:
        query = query.filter(SummaryUsage.date <= end_date)
    if model:
        query = query.filter(SummaryUsage.model == model)

    stats = query.first()

    if stats is None:
        return {
            "total_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "average_processing_time": 0.0,
        }

    return {
        "total_count": int(stats[0]) if stats[0] is not None else 0,
        "total_input_tokens": int(stats[1]) if stats[1] is not None else 0,
        "total_output_tokens": int(stats[2]) if stats[2] is not None else 0,
        "average_processing_time": round(float(stats[3]), 2) if stats[3] is not None else 0.0,
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
        .order_by(desc("count"))
        .all()
    )

    return [
        {
            "document_type": r.document_type or "-",
            "department": "全科共通" if r.department == "default" else (r.department or "全科共通"),
            "doctor": "医師共通" if r.doctor == "default" else (r.doctor or "医師共通"),
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
