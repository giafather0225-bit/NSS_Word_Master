from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, Index
try:
    from .database import Base
except ImportError:
    from database import Base  # when run directly from backend/


class Lesson(Base):
    """레슨(단원) 메타데이터 — 수동 입력/OCR 구분 및 교재·단원 관리."""
    __tablename__ = "lessons"

    id          = Column(Integer, primary_key=True, index=True)
    subject     = Column(String, index=True)              # e.g., "English", "Math"
    textbook    = Column(String, index=True, default="")  # e.g., "Voca_8000"
    lesson_name = Column(String, index=True)              # e.g., "Lesson_09"
    source_type = Column(String, default="ocr")           # "manual" | "ocr" | "file"
    description = Column(String, default="")
    created_at  = Column(String)                          # ISO 8601 datetime string

    __table_args__ = (
        Index("ix_lessons_subject_textbook_name", "subject", "textbook", "lesson_name"),
    )


class StudyItem(Base):
    __tablename__ = "study_items"

    id          = Column(Integer, primary_key=True, index=True)
    subject     = Column(String, index=True)              # e.g., "English", "Math"
    textbook    = Column(String, index=True, default="")  # e.g., "Voca_8000"
    lesson      = Column(String, index=True)              # e.g., "Lesson_09"
    lesson_id   = Column(Integer, ForeignKey("lessons.id"), nullable=True, index=True)
    source_type = Column(String, default="ocr")           # "manual" | "ocr"
    question    = Column(String)                          # definition or math question
    answer      = Column(String, index=True)              # correct spelling or math solution
    hint        = Column(String)                          # example sentence with blank
    extra_data  = Column(String)                          # JSON: pos, image, etc.

    __table_args__ = (
        Index("ix_study_items_subject_textbook_lesson", "subject", "textbook", "lesson"),
    )

class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True)
    textbook = Column(String, index=True, default="")  # e.g., "Voca_8000"
    lesson = Column(String, index=True)
    current_index = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_progress_subject_textbook_lesson", "subject", "textbook", "lesson"),
    )
    
class Reward(Base):
    __tablename__ = "rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    is_earned = Column(Boolean, default=False)
    
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    test_date = Column(String) # YYYY-MM-DD format
    memo = Column(String)


class UserPracticeSentence(Base):
    """Step 2에서 학생이 작성한 문장 — Perfect Challenge 출제 풀."""
    __tablename__ = "user_practice_sentences"

    id       = Column(Integer, primary_key=True, index=True)
    subject  = Column(String, index=True)
    textbook = Column(String, index=True, default="")  # e.g., "Voca_8000"
    lesson   = Column(String, index=True)
    item_id  = Column(Integer, index=True)  # study_items.id
    sentence = Column(String)

    __table_args__ = (
        Index("ix_practice_sentences_subject_textbook_lesson", "subject", "textbook", "lesson"),
    )


class Word(Base):
    """OCR 파이프라인이 추출한 단어 원본 레코드.

    study_items 와 1:1 연결 가능 (study_item_id).
    단순한 word/definition/example 스키마 유지 — 앱 학습 흐름은 study_items 사용.
    """
    __tablename__ = "words"

    id             = Column(Integer, primary_key=True, index=True)
    word           = Column(String, index=True)
    definition     = Column(String)
    example        = Column(String)
    pos            = Column(String, default="")
    lesson_id      = Column(Integer, ForeignKey("lessons.id"), nullable=True, index=True)
    study_item_id  = Column(Integer, ForeignKey("study_items.id"), nullable=True, index=True)
    source_type    = Column(String, default="ocr")   # "ocr" | "manual"
    ocr_engine     = Column(String, default="")      # "tesseract" | "vision" | ""
    created_at     = Column(String)                  # ISO 8601


class WordReview(Base):
    """SM-2 spaced repetition tracking per word."""
    __tablename__ = "word_reviews"

    id             = Column(Integer, primary_key=True, index=True)
    study_item_id  = Column(Integer, ForeignKey("study_items.id"), nullable=False, index=True)
    word           = Column(String, index=True)
    subject        = Column(String, default="English")
    textbook       = Column(String, default="")
    lesson         = Column(String, default="")

    easiness       = Column(String, default="2.5")
    interval       = Column(Integer, default=0)
    repetitions    = Column(Integer, default=0)
    next_review    = Column(String)
    last_review    = Column(String, default="")

    total_reviews  = Column(Integer, default=0)
    total_correct  = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_word_reviews_next_review", "next_review"),
        Index("ix_word_reviews_subject_textbook", "subject", "textbook"),
    )


class AppConfig(Base):
    """앱 전역 설정 (PIN, 이메일, 테마 등)"""
    __tablename__ = "app_config"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    updated_at = Column(String)

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

class DiaryEntry(Base):
    """GIA's Diary — Daily Journal"""
    __tablename__ = "diary_entries"
    id = Column(Integer, primary_key=True)
    entry_date = Column(String, index=True)
    content = Column(String)
    photo_path = Column(String, nullable=True)
    ai_feedback = Column(String, nullable=True)
    created_at = Column(String)

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

class AcademySession(Base):
    """Academy 레슨 진행 세션"""
    __tablename__ = "academy_sessions"
    id = Column(Integer, primary_key=True)
    subject = Column(String)
    textbook = Column(String)
    lesson = Column(String)
    started_date = Column(String)
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


# ── Math Section Models ───────────────────────────────────────

class MathPlacementResult(Base):
    """Math placement test results per domain."""
    __tablename__ = "math_placement_results"
    id = Column(Integer, primary_key=True)
    test_date = Column(String, index=True)
    domain = Column(String)
    estimated_grade = Column(String)
    rit_estimate = Column(Integer, nullable=True)
    raw_score = Column(Integer)
    total_questions = Column(Integer)
    detail_json = Column(String, default="{}")


class MathProblem(Base):
    """Math problem bank — stores all problems as JSON."""
    __tablename__ = "math_problems"
    id = Column(Integer, primary_key=True)
    problem_id = Column(String, unique=True, index=True)
    grade = Column(String, index=True)
    unit = Column(String, index=True)
    lesson = Column(String, index=True)
    stage = Column(String)
    type = Column(String)
    difficulty = Column(Integer, default=1)
    concept = Column(String, default="")
    question_json = Column(String, default="{}")
    tags_json = Column(String, default="[]")
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_math_problems_grade_unit_lesson", "grade", "unit", "lesson"),
    )


class MathProgress(Base):
    """Math academy lesson progress tracking."""
    __tablename__ = "math_progress"
    id = Column(Integer, primary_key=True)
    grade = Column(String, index=True)
    unit = Column(String, index=True)
    lesson = Column(String, index=True)
    stage = Column(String, default="pretest")
    is_completed = Column(Boolean, default=False)
    pretest_score = Column(Integer, nullable=True)
    pretest_passed = Column(Boolean, default=False)
    pretest_skipped = Column(Boolean, default=False)
    best_score_r1 = Column(Integer, nullable=True)
    best_score_r2 = Column(Integer, nullable=True)
    best_score_r3 = Column(Integer, nullable=True)
    unit_test_score = Column(Integer, nullable=True)
    unit_test_passed = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    last_accessed = Column(String)

    __table_args__ = (
        Index("ix_math_progress_grade_unit_lesson", "grade", "unit", "lesson"),
    )


class MathAttempt(Base):
    """Individual math problem attempt records."""
    __tablename__ = "math_attempts"
    id = Column(Integer, primary_key=True)
    problem_id = Column(String, index=True)
    grade = Column(String)
    unit = Column(String)
    lesson = Column(String)
    stage = Column(String)
    is_correct = Column(Boolean)
    user_answer = Column(String, default="")
    error_type = Column(String, default="concept_gap")
    time_spent_sec = Column(Integer, default=0)
    attempted_at = Column(String)


class MathWrongReview(Base):
    """Spaced repetition for wrong math problems."""
    __tablename__ = "math_wrong_review"
    id = Column(Integer, primary_key=True)
    problem_id = Column(String, index=True)
    original_attempt_id = Column(Integer, nullable=True)
    next_review_date = Column(String, index=True)
    interval_days = Column(Integer, default=1)
    times_reviewed = Column(Integer, default=0)
    is_mastered = Column(Boolean, default=False)


class MathFactFluency(Base):
    """Fact fluency progress per fact set."""
    __tablename__ = "math_fact_fluency"
    id = Column(Integer, primary_key=True)
    fact_set = Column(String, unique=True, index=True)
    current_phase = Column(String, default="A")
    best_score = Column(Integer, default=0)
    best_time_sec = Column(Integer, default=0)
    accuracy_pct = Column(Float, default=0.0)
    total_rounds = Column(Integer, default=0)
    last_played = Column(String, nullable=True)


class MathDailyChallenge(Base):
    """Daily math challenge records."""
    __tablename__ = "math_daily_challenge"
    id = Column(Integer, primary_key=True)
    challenge_date = Column(String, unique=True, index=True)
    problems_json = Column(String, default="[]")
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    completed = Column(Boolean, default=False)


class MathKangarooProgress(Base):
    """Math Kangaroo practice set progress."""
    __tablename__ = "math_kangaroo_progress"
    id = Column(Integer, primary_key=True)
    set_id = Column(String, unique=True, index=True)
    category = Column(String, default="")
    difficulty_level = Column(String, default="pre_ecolier")
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    completed_at = Column(String, nullable=True)
