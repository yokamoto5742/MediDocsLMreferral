from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True)
    department = Column(String(100), nullable=False)
    document_type = Column(String(100), nullable=False)
    doctor = Column(String(100), nullable=False)
    content = Column(Text)
    selected_model = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
