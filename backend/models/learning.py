"""
models/learning.py — Daily Words, Academy sessions, learning logs, attempts.
Section: English
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from ._base import Base


class DailyWordsProgress(Base):
    """Daily Words 학습 진행"""
    __tablename__ = "daily_words_progress"
    id = Column(Integer, primary_key=True)
    grade = Column(String)
    cycle_start = Column(String)
    word_index = Column(Integer, default=0)
    test_words_json = Column(String)
    daily_learned = Column(Integer, default=0)
    last_study_date = Column(String)


class AcademySession(Base):
    """Academy 레슨 진행 세션"""
    __tablename__ = "academy_sessions"
    id = Column(Integer, primary_key=True)
    subject = Column(String)
    textbook = Column(String)
    lesson = Column(String)
    started_date = Column(String)
    last_active_date = Column(String, index=True)
    current_stage = Column(String, default="PREVIEW")
    is_completed = Column(Boolean, default=False)
    is_reset = Column(Boolean, default=False)


class LearningLog(Base):
    """학습 로그"""
    __tablename__ = "learning_logs"
    id = Column(Integer, primary_key=True)
    subject = Column(String, default="English")
    textbook = Column(String)
    lesson = Column(String)
    stage = Column(String)
    word_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    wrong_words_json = Column(String)
    started_at = Column(String)
    completed_at = Column(String)
    duration_sec = Column(Integer, default=0)


class WordAttempt(Base):
    """단어별 시도 기록"""
    __tablename__ = "word_attempts"
    id = Column(Integer, primary_key=True)
    study_item_id = Column(Integer, ForeignKey("study_items.id"), nullable=True)
    subject = Column(String, default="English")
    textbook = Column(String)
    lesson = Column(String)
    word = Column(String)
    stage = Column(String)
    is_correct = Column(Boolean)
    user_answer = Column(String)
    attempted_at = Column(String)


class AcademySchedule(Base):
    """학원 시험 스케줄"""
    __tablename__ = "academy_schedules"
    id = Column(Integer, primary_key=True)
    day_of_week = Column(Integer)
    memo = Column(String)
    is_active = Column(Boolean, default=True)


__all__ = [
    "DailyWordsProgress",
    "AcademySession",
    "LearningLog",
    "WordAttempt",
    "AcademySchedule",
]
