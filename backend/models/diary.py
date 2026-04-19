"""
models/diary.py — GIA's Diary (Journal, Free Writing, Growth, Day Off).
Section: Diary
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String

from ._base import Base


class DiaryEntry(Base):
    """GIA's Diary — Daily Journal"""
    __tablename__ = "diary_entries"
    id = Column(Integer, primary_key=True)
    entry_date = Column(String, index=True)
    content = Column(String)
    photo_path = Column(String, nullable=True)
    ai_feedback = Column(String, nullable=True)
    created_at = Column(String)


class FreeWriting(Base):
    """GIA's Diary — Free Writing entries (open-ended creative writing, no date constraint)."""
    __tablename__ = "free_writings"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    ai_feedback = Column(String, nullable=True)
    created_at = Column(String, index=True)


class GrowthEvent(Base):
    """My Growth — Growth Timeline 이벤트"""
    __tablename__ = "growth_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, index=True)
    title = Column(String)
    detail = Column(String)
    event_date = Column(String, index=True)
    created_at = Column(String)


class DayOffRequest(Base):
    """Day Off 사유서"""
    __tablename__ = "day_off_requests"
    id = Column(Integer, primary_key=True)
    request_date = Column(String, index=True)
    reason = Column(String)
    status = Column(String, default="pending")
    parent_response = Column(String, nullable=True)
    created_at = Column(String)


__all__ = ["DiaryEntry", "FreeWriting", "GrowthEvent", "DayOffRequest"]
