from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from app.core.database import Base

class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_source = Column(String(100), nullable=False, default="general")
    analysis_goal = Column(String(100), nullable=False, default="general")
    language = Column(String(50), nullable=False, default="auto")
    item_count = Column(Integer, default=0)
    raw_sample = Column(Text, nullable=True)
    status = Column(String(20), default="completed")  # completed, failed
    social_metadata = Column(JSON, nullable=True)
    result = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_source": self.feedback_source,
            "analysis_goal": self.analysis_goal,
            "language": self.language,
            "item_count": self.item_count,
            "raw_sample": self.raw_sample,
            "status": self.status,
            "social_metadata": self.social_metadata,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
