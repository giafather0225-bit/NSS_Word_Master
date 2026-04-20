"""
models/math.py — Math section models (placement, problems, progress, attempts, fluency).
Section: Math
Dependencies: ._base.Base
"""

from sqlalchemy import Column, Integer, Float, String, Boolean, Index

from ._base import Base


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
    level = Column(String, default="")
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, nullable=True)
    answers_json = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)


__all__ = [
    "MathPlacementResult",
    "MathProblem",
    "MathProgress",
    "MathAttempt",
    "MathWrongReview",
    "MathFactFluency",
    "MathDailyChallenge",
    "MathKangarooProgress",
]
