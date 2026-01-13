from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from .base import Base


class SummaryUsage(Base):
    __tablename__ = "summary_usage"

    id = Column(Integer, primary_key=True)
    department = Column(String(100))
    doctor = Column(String(100))
    document_type = Column(String(100))
    model = Column(String(50))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    processing_time = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
