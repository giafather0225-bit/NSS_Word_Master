"""
models/system.py — System tables (Schedule, AppConfig).
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String

from ._base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(String)  # YYYY-MM-DD format
    memo = Column(String)


class AppConfig(Base):
    """App-wide settings (PIN, email, theme, etc.)"""
    __tablename__ = "app_config"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    updated_at = Column(String)


__all__ = ["Schedule", "AppConfig"]
