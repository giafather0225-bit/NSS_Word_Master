"""
models/gamification.py — XP, Streak, Tasks, Reward Shop, Growth Theme.
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Index, Integer, String, Boolean, ForeignKey

from ._base import Base


class XPLog(Base):
    """XP earning record"""
    __tablename__ = "xp_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String)
    xp_amount = Column(Integer)
    detail = Column(String)
    earned_date = Column(String)
    created_at = Column(String)
    source = Column(String)  # e.g. "ckla", "math", "english", "diary"

    # Composite index for the daily-dedup query in xp_engine.award_xp():
    # WHERE action = ? AND earned_date = ? [AND detail = ?]
    # Without this index every award_xp() call scans the full xp_logs table.
    __table_args__ = (
        Index("ix_xplog_action_date", "action", "earned_date"),
    )


class StreakLog(Base):
    """Streak record"""
    __tablename__ = "streak_logs"
    id = Column(Integer, primary_key=True)
    date = Column(String, unique=True, index=True)
    review_done = Column(Boolean, default=False)
    daily_words_done = Column(Boolean, default=False)
    math_done = Column(Boolean, default=False)
    game_done = Column(Boolean, default=False)
    ckla_done = Column(Boolean, default=False)
    streak_maintained = Column(Boolean, default=False)


class TaskSetting(Base):
    """Today's Tasks configured by the parent"""
    __tablename__ = "task_settings"
    id = Column(Integer, primary_key=True)
    task_key = Column(String, unique=True, index=True)
    is_required = Column(Boolean, default=False)
    xp_value = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class RewardItem(Base):
    """Reward shop item"""
    __tablename__ = "reward_items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String, default="")
    category = Column(String, default="badge")  # "badge", "theme", "power", "real"
    icon = Column(String)
    price = Column(Integer)
    discount_pct = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(String)


class PurchasedReward(Base):
    """Purchased reward"""
    __tablename__ = "purchased_rewards"
    id = Column(Integer, primary_key=True)
    reward_item_id = Column(Integer, ForeignKey("reward_items.id"))
    xp_spent = Column(Integer)
    is_used = Column(Boolean, default=False)
    is_equipped = Column(Boolean, default=False)
    purchased_at = Column(String)
    used_at = Column(String, nullable=True)


__all__ = [
    "XPLog",
    "StreakLog",
    "TaskSetting",
    "RewardItem",
    "PurchasedReward",
]
