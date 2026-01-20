from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UsageSummary(BaseModel):
    total_count: int
    total_input_tokens: int
    total_output_tokens: int
    average_processing_time: float


class UsageRecord(BaseModel):
    id: int
    date: datetime | None
    app_type: str | None
    document_type: str | None
    model: str | None
    department: str | None
    doctor: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    processing_time: float | None

    model_config = ConfigDict(from_attributes=True)


class AggregatedRecord(BaseModel):
    """集計レコード"""
    document_type: str
    department: str
    doctor: str
    count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int

    model_config = ConfigDict(from_attributes=True)
