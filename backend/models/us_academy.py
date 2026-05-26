"""
models/us_academy.py — US Academy word/progress ORM models.
Section: Academy
Dependencies: ._base.Base

Tables (active):
  us_academy_words        — 684 CKLA G3 academic words
  us_academy_word_progress — per-word 5-step learning progress + SM-2

Removed (migrations 047, 048):
  us_academy_passages     — CLEAR Corpus passages — dropped (0 rows, replaced by CKLA)
  us_academy_sessions     — original US Academy sessions — dropped (0 rows, dead code)
  us_academy_unit_results — original US Academy unit results — dropped (0 rows, dead code)
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text

from ._base import Base


class USAcademyWord(Base):
    """300 academic words — includes Merriam-Webster + WordNet data"""
    __tablename__ = "us_academy_words"

    id              = Column(Integer, primary_key=True)
    word            = Column(String, nullable=False, index=True)
    level           = Column(Integer, nullable=False, index=True)   # 1, 2, 3
    category        = Column(String, nullable=False)                # "thinking", "connecting", "text", "ela", "math", "science", "social"
    sort_order      = Column(Integer, default=0)                    # order within category

    # Merriam-Webster Elementary API data
    definition      = Column(Text)       # English-to-English definition (child-friendly)
    part_of_speech  = Column(String)     # noun, verb, adjective ...
    audio_url       = Column(String)     # MW pronunciation audio URL
    example_1       = Column(Text)       # curriculum example sentence 1
    example_2       = Column(Text)       # curriculum example sentence 2 (different subject context)

    # WordNet data
    synonyms_json   = Column(String)     # JSON list of synonyms
    antonyms_json   = Column(String)     # JSON list of antonyms

    # Manual curation
    morphology      = Column(String)     # e.g. "pre- (before) + dict (say)"
    word_family     = Column(String)     # e.g. "predict, prediction, predictable"

    is_active       = Column(Boolean, default=True)


class USAcademyWordProgress(Base):
    """Per-word 5-step study progress + SM-2 spaced repetition"""
    __tablename__ = "us_academy_word_progress"

    id              = Column(Integer, primary_key=True)
    word_id         = Column(Integer, nullable=False, index=True)
    word            = Column(String, nullable=False)

    # 5-step completion flags
    step_meet_it    = Column(Boolean, default=False)   # (1) read the definition
    step_see_it     = Column(Boolean, default=False)   # (2) read example sentences
    step_use_it     = Column(Boolean, default=False)   # (3) fill in the blank
    step_know_it    = Column(Boolean, default=False)   # (4) pick synonym/antonym
    step_own_it     = Column(Boolean, default=False)   # (5) pick the correct usage
    steps_completed = Column(Integer, default=0)       # 0-5

    # SM-2 fields (reusing sm2.py logic)
    sm2_repetitions = Column(Integer, default=0)
    sm2_easiness    = Column(Float, default=2.5)
    sm2_interval    = Column(Integer, default=1)
    next_review     = Column(String, index=True)       # ISO date string

    # Stats
    correct_count   = Column(Integer, default=0)
    wrong_count     = Column(Integer, default=0)
    last_studied    = Column(String)


__all__ = [
    "USAcademyWord",
    "USAcademyWordProgress",
]
