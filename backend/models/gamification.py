"""
models/gamification.py — XP, Streak, Tasks, Reward Shop, Growth Theme.
Section: System
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from ._base import Base


class XPLog(Base):
    """XP 획득 기록"""
    __tablename__ = "xp_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String)
    xp_amount = Column(Integer)
    detail = Column(String)
    earned_date = Column(String)
    created_at = Column(String)


class StreakLog(Base):
    """Streak 기록"""
    __tablename__ = "streak_logs"
    id = Column(Integer, primary_key=True)
    date = Column(String, unique=True, index=True)
    review_done = Column(Boolean, default=False)
    daily_words_done = Column(Boolean, default=False)
    math_done = Column(Boolean, default=False)
    game_done = Column(Boolean, default=False)
    streak_maintained = Column(Boolean, default=False)


class TaskSetting(Base):
    """부모가 설정한 Today's Tasks"""
    __tablename__ = "task_settings"
    id = Column(Integer, primary_key=True)
    task_key = Column(String, unique=True, index=True)
    is_required = Column(Boolean, default=False)
    xp_value = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class RewardItem(Base):
    """보상 상점 아이템"""
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
    """구매된 보상"""
    __tablename__ = "purchased_rewards"
    id = Column(Integer, primary_key=True)
    reward_item_id = Column(Integer, ForeignKey("reward_items.id"))
    xp_spent = Column(Integer)
    is_used = Column(Boolean, default=False)
    is_equipped = Column(Boolean, default=False)
    purchased_at = Column(String)
    used_at = Column(String, nullable=True)


class GrowthThemeProgress(Base):
    """성장 테마 진행 추적"""
    __tablename__ = "growth_theme_progress"
    id = Column(Integer, primary_key=True)
    theme = Column(String)
    variation = Column(Integer, default=1)
    current_step = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    started_at = Column(String)
    completed_at = Column(String, nullable=True)


__all__ = [
    "XPLog",
    "StreakLog",
    "TaskSetting",
    "RewardItem",
    "PurchasedReward",
    "GrowthThemeProgress",
]
