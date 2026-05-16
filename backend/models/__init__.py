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
    MathSpacedReview,
    MathUnitTest,
    MathPlacementTest,
)
from .assistant import AssistantLog, AiCallLog
from .us_academy import (
    USAcademyWord,
    USAcademyWordProgress,
)
from .ckla import (
    CKLADomain,
    CKLALesson,
    CKLAQuestion,
    CKLAWordLesson,
    CKLALessonProgress,
    CKLAQuestionResponse,
    CKLABadge,
    CKLAUserBadge,
    CKLASpelling,
    CKLAGrammar,
    CKLAMorphology,
)

__all__ = [
    "Base",
    # lessons
    "Lesson", "StudyItem", "Progress", "UserPracticeSentence", "Word", "WordReview",
    # system
    "Reward", "Schedule", "AppConfig",
    # gamification
    "XPLog", "StreakLog", "TaskSetting", "RewardItem", "PurchasedReward",
    # learning
    "DailyWordsProgress", "AcademySession", "LearningLog", "WordAttempt", "AcademySchedule",
    # diary
    "DiaryEntry", "FreeWriting", "GrowthEvent", "DayOffRequest",
    # math
    "MathPlacementResult", "MathProblem", "MathProgress", "MathAttempt",
    "MathWrongReview", "MathFactFluency", "MathDailyChallenge", "MathKangarooProgress",
    "MathSpacedReview", "MathUnitTest", "MathPlacementTest",
    # assistant / ai audit
    "AssistantLog", "AiCallLog",
    # us academy words (active — used by CKLA)
    "USAcademyWord", "USAcademyWordProgress",
    # ckla (passage-centric)
    "CKLADomain", "CKLALesson", "CKLAQuestion",
    "CKLAWordLesson", "CKLALessonProgress", "CKLAQuestionResponse",
    "CKLABadge", "CKLAUserBadge",
    "CKLASpelling", "CKLAGrammar", "CKLAMorphology",
    # island
    "IslandCharacter", "IslandCharacterProgress", "IslandCareLog",
    "IslandShopItem", "IslandInventory", "IslandPlacedItem",
    "IslandCurrency", "IslandLumiLog", "IslandLegendProgress", "IslandZoneStatus",
]
from backend.models.goals import WeeklyGoal
from .island import (
    IslandCharacter,
    IslandCharacterProgress,
    IslandCareLog,
    IslandShopItem,
    IslandInventory,
    IslandPlacedItem,
    IslandCurrency,
    IslandLumiLog,
    IslandLegendProgress,
    IslandZoneStatus,
)
