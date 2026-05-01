"""
models/ckla.py — CKLA ORM models (grade-aware)
Section: Academy
Dependencies: ._base.Base, migrations 011, 019, 020, 021

Tables (created/modified by migrations 011, 019, 020, 021):
  us_academy_domains          — CKLA domains (grade-aware)
  us_academy_lessons          — lessons (passage + Word Work, grade-aware)
  us_academy_questions        — comprehension questions
  us_academy_word_lesson      — word ↔ lesson N:M link
  us_academy_lesson_progress  — per-lesson progress (grade, started_at, difficulty_rating)
  us_academy_question_responses — per-question answer records
  ckla_badges                 — badge catalog (migration 020)
  ckla_user_badges            — user earned badges (migration 020)
  ckla_spelling               — weekly spelling word lists (migration 021)
  ckla_grammar                — grammar topics per unit (migration 021)
  ckla_morphology             — morphology topics per unit (migration 021)
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey

from ._base import Base


class CKLADomain(Base):
    """CKLA domain (11 per grade)"""
    __tablename__ = "us_academy_domains"

    id           = Column(Integer, primary_key=True)
    domain_num   = Column(Integer, nullable=False)   # 1~11
    title        = Column(String, nullable=False)
    source_pdf   = Column(String)
    lesson_count = Column(Integer, default=0)
    is_active    = Column(Boolean, default=True)
    grade        = Column(Integer, nullable=False, default=3)


class CKLALesson(Base):
    """CKLA lesson — passage + Word Work"""
    __tablename__ = "us_academy_lessons"

    id             = Column(Integer, primary_key=True)
    domain_id      = Column(Integer, ForeignKey("us_academy_domains.id"), nullable=False)
    domain_num     = Column(Integer, nullable=False)
    lesson_num     = Column(Integer, nullable=False)
    title          = Column(String, nullable=False)
    passage        = Column(Text, nullable=False)
    passage_chars  = Column(Integer, default=0)
    word_work_word = Column(String)
    is_active      = Column(Boolean, default=True)
    grade          = Column(Integer, nullable=False, default=3)


class CKLAQuestion(Base):
    """Comprehension questions (Literal / Inferential / Evaluative)"""
    __tablename__ = "us_academy_questions"

    id            = Column(Integer, primary_key=True)
    lesson_id     = Column(Integer, ForeignKey("us_academy_lessons.id"), nullable=False)
    question_num  = Column(Integer, nullable=False)
    kind          = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    model_answer  = Column(Text)


class CKLAWordLesson(Base):
    """Word ↔ lesson N:M link"""
    __tablename__ = "us_academy_word_lesson"

    id        = Column(Integer, primary_key=True)
    word_id   = Column(Integer, ForeignKey("us_academy_words.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("us_academy_lessons.id"), nullable=False)


class CKLALessonProgress(Base):
    """Per-lesson learning progress"""
    __tablename__ = "us_academy_lesson_progress"

    id                  = Column(Integer, primary_key=True)
    lesson_id           = Column(Integer, ForeignKey("us_academy_lessons.id"), unique=True)
    reading_done        = Column(Boolean, default=False)
    reading_done_at     = Column(String)
    vocab_done          = Column(Boolean, default=False)
    questions_attempted = Column(Integer, default=0)
    questions_correct   = Column(Integer, default=0)
    word_work_done      = Column(Boolean, default=False)
    completed           = Column(Boolean, default=False)
    completed_at        = Column(String)
    last_active         = Column(String)
    # migration 019
    grade               = Column(Integer, nullable=False, default=3)
    started_at          = Column(String)
    difficulty_rating   = Column(String)   # "easy" / "neutral" / "hard"


class CKLAQuestionResponse(Base):
    """Per-question answer record (AI graded)"""
    __tablename__ = "us_academy_question_responses"

    id                  = Column(Integer, primary_key=True)
    question_id         = Column(Integer, ForeignKey("us_academy_questions.id"), nullable=False)
    lesson_progress_id  = Column(Integer, ForeignKey("us_academy_lesson_progress.id"))
    user_answer         = Column(Text)
    ai_score            = Column(Integer, default=0)   # 0=wrong, 1=partial, 2=correct
    ai_feedback         = Column(Text)
    needs_parent_review = Column(Boolean, default=False)
    created_at          = Column(String)


class CKLABadge(Base):
    """Badge catalog (migration 020)"""
    __tablename__ = "ckla_badges"

    id              = Column(Integer, primary_key=True)
    badge_key       = Column(String, unique=True, nullable=False)
    badge_name      = Column(String, nullable=False)
    description     = Column(String, nullable=False)
    condition_type  = Column(String, nullable=False)   # "domain_complete" / "grade_complete"
    condition_value = Column(Integer, nullable=False)   # domain_num or grade
    image_path      = Column(String)
    created_at      = Column(String)


class CKLAUserBadge(Base):
    """User earned badges — UNIQUE on badge_key (no duplicates)"""
    __tablename__ = "ckla_user_badges"

    id        = Column(Integer, primary_key=True)
    badge_key = Column(String, unique=True, nullable=False)
    earned_at = Column(String, nullable=False)


class CKLASpelling(Base):
    """Weekly spelling word lists per unit (migration 021)"""
    __tablename__ = "ckla_spelling"

    id              = Column(Integer, primary_key=True)
    unit            = Column(Integer, nullable=False)
    week            = Column(Integer, nullable=False)
    pattern         = Column(String, nullable=False, default="")
    words           = Column(Text, nullable=False, default="[]")    # JSON array
    challenge_words = Column(Text, nullable=False, default="[]")    # JSON array


class CKLAGrammar(Base):
    """Grammar topics per unit (migration 021)"""
    __tablename__ = "ckla_grammar"

    id     = Column(Integer, primary_key=True)
    unit   = Column(Integer, nullable=False, unique=True)
    topics = Column(Text, nullable=False, default="[]")    # JSON array


class CKLAMorphology(Base):
    """Morphology topics per unit (migration 021)"""
    __tablename__ = "ckla_morphology"

    id     = Column(Integer, primary_key=True)
    unit   = Column(Integer, nullable=False, unique=True)
    topics = Column(Text, nullable=False, default="[]")    # JSON array


__all__ = [
    "CKLADomain",
    "CKLALesson",
    "CKLAQuestion",
    "CKLAWordLesson",
    "CKLALessonProgress",
    "CKLAQuestionResponse",
    "CKLABadge",
    "CKLAUserBadge",
    "CKLASpelling",
    "CKLAGrammar",
    "CKLAMorphology",
]
