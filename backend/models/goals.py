"""
models/goals.py — WeeklyGoal ORM model
Section: Parent
"""
from __future__ import annotations
from sqlalchemy import Column, Integer, String
from backend.database import Base


class WeeklyGoal(Base):
    __tablename__ = "weekly_goals"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    key        = Column(String,  nullable=False, unique=True)
    label      = Column(String,  nullable=False)
    target     = Column(Integer, nullable=False, default=0)
    is_active  = Column(Integer, nullable=False, default=1)
    updated_at = Column(String,  nullable=False)
