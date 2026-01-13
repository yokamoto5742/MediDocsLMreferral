from datetime import datetime
from pydantic import BaseModel


class UsageSummary(BaseModel):
    total_count: int
    total_input_tokens: int
    total_output_tokens: int
    average_processing_time: float


class UsageRecord(BaseModel):
    id: int
    department: str | None
    doctor: str | None
    document_type: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    processing_time: float | None
    created_at: datetime | None

    class Config:
        from_attributes = True
