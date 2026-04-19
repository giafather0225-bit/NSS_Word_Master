"""
models/system.py — System + legacy (Reward, Schedule, AppConfig).
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String, Boolean

from ._base import Base


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    is_earned = Column(Boolean, default=False)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(String)  # YYYY-MM-DD format
    memo = Column(String)


class AppConfig(Base):
    """앱 전역 설정 (PIN, 이메일, 테마 등)"""
    __tablename__ = "app_config"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    updated_at = Column(String)


__all__ = ["Reward", "Schedule", "AppConfig"]
