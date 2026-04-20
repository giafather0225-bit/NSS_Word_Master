"""
models/ — SQLAlchemy ORM models split by domain.
Section: System
Dependencies: database.Base

Re-exports every model class so legacy `from backend.models import X` /
`from ..models import X` imports continue working unchanged.
"""

from ._base import Base
from .lessons import (
    Lesson,
    StudyItem,
    Progress,
    UserPracticeSentence,
    Word,
    WordReview,
)
from .system import Reward, Schedule, AppConfig
from .gamification import (
    XPLog,
    StreakLog,
    TaskSetting,
    RewardItem,
    PurchasedReward,
    GrowthThemeProgress,
)
from .learning import (
    DailyWordsProgress,
    AcademySession,
    LearningLog,
    WordAttempt,
    AcademySchedule,
)
from .diary import DiaryEntry, FreeWriting, GrowthEvent, DayOffRequest
from .math import (
    MathPlacementResult,
    MathProblem,
    MathProgress,
    MathAttempt,
    MathWrongReview,
    MathFactFluency,
    MathDailyChallenge,
    MathKangarooProgress,
)
from .assistant import AssistantLog

__all__ = [
    "Base",
    # lessons
    "Lesson", "StudyItem", "Progress", "UserPracticeSentence", "Word", "WordReview",
    # system
    "Reward", "Schedule", "AppConfig",
    # gamification
    "XPLog", "StreakLog", "TaskSetting", "RewardItem", "PurchasedReward", "GrowthThemeProgress",
    # learning
    "DailyWordsProgress", "AcademySession", "LearningLog", "WordAttempt", "AcademySchedule",
    # diary
    "DiaryEntry", "FreeWriting", "GrowthEvent", "DayOffRequest",
    # math
    "MathPlacementResult", "MathProblem", "MathProgress", "MathAttempt",
    "MathWrongReview", "MathFactFluency", "MathDailyChallenge", "MathKangarooProgress",
    # assistant
    "AssistantLog",
]
