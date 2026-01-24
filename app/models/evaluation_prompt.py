from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class EvaluationPrompt(Base):
    __tablename__ = "evaluation_prompts"

    id = Column(Integer, primary_key=True)
    document_type = Column(String(100), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
