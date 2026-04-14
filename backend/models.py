from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from .database import Base


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
