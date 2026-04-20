"""
models/assistant.py — Models for Shadow Assistant (V2)
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ._base import Base

class AssistantLog(Base):
    __tablename__ = "assistant_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_message = Column(String)
    assistant_reply = Column(String)
    was_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

__all__ = ["AssistantLog"]
