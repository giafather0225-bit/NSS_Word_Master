"""
models/ckla.py — CKLA G3 ORM models
Section: Academy
Dependencies: ._base.Base, migration 011_ckla_tables.py

Tables (created by migration 011):
  us_academy_domains          — 11 CKLA 도메인
  us_academy_lessons          — 104 레슨 (passage + Word Work)
  us_academy_questions        — 819 문제 (Literal/Inferential/Evaluative)
  us_academy_word_lesson      — 단어 ↔ 레슨 N:M 링크
  us_academy_lesson_progress  — 레슨별 학습 진행 상태
  us_academy_question_responses — 문제별 답변 기록
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey

from ._base import Base


class CKLADomain(Base):
    """CKLA G3 도메인 (11개)"""
    __tablename__ = "us_academy_domains"

    id           = Column(Integer, primary_key=True)
    domain_num   = Column(Integer, nullable=False, unique=True)   # 1~11
    title        = Column(String, nullable=False)
    source_pdf   = Column(String)
    lesson_count = Column(Integer, default=0)
    is_active    = Column(Boolean, default=True)


class CKLALesson(Base):
    """CKLA 레슨 (104개) — 지문 + Word Work"""
    __tablename__ = "us_academy_lessons"

    id             = Column(Integer, primary_key=True)
    domain_id      = Column(Integer, ForeignKey("us_academy_domains.id"), nullable=False)
    domain_num     = Column(Integer, nullable=False)
    lesson_num     = Column(Integer, nullable=False)
    title          = Column(String, nullable=False)
    passage        = Column(Text, nullable=False)
    passage_chars  = Column(Integer, default=0)
    word_work_word = Column(String)                # 집중 단어 1개
    is_active      = Column(Boolean, default=True)


class CKLAQuestion(Base):
    """이해 문제 (819개)"""
    __tablename__ = "us_academy_questions"

    id            = Column(Integer, primary_key=True)
    lesson_id     = Column(Integer, ForeignKey("us_academy_lessons.id"), nullable=False)
    question_num  = Column(Integer, nullable=False)
    kind          = Column(String, nullable=False)   # Literal / Inferential / Evaluative
    question_text = Column(Text, nullable=False)
    model_answer  = Column(Text)


class CKLAWordLesson(Base):
    """단어 ↔ 레슨 N:M 링크"""
    __tablename__ = "us_academy_word_lesson"

    id        = Column(Integer, primary_key=True)
    word_id   = Column(Integer, ForeignKey("us_academy_words.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("us_academy_lessons.id"), nullable=False)


class CKLALessonProgress(Base):
    """레슨별 학습 진행 상태"""
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


class CKLAQuestionResponse(Base):
    """문제별 답변 기록 (AI 채점 포함)"""
    __tablename__ = "us_academy_question_responses"

    id                  = Column(Integer, primary_key=True)
    question_id         = Column(Integer, ForeignKey("us_academy_questions.id"), nullable=False)
    lesson_progress_id  = Column(Integer, ForeignKey("us_academy_lesson_progress.id"))
    user_answer         = Column(Text)
    ai_score            = Column(Integer, default=0)   # 0=틀림, 1=부분정답, 2=정답
    ai_feedback         = Column(Text)
    needs_parent_review = Column(Boolean, default=False)
    created_at          = Column(String)


__all__ = [
    "CKLADomain",
    "CKLALesson",
    "CKLAQuestion",
    "CKLAWordLesson",
    "CKLALessonProgress",
    "CKLAQuestionResponse",
]
