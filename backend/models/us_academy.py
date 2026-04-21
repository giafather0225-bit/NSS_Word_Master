"""
models/us_academy.py — US Academy (미국학교 대비) ORM models.
Section: Academy
Dependencies: ._base.Base

Tables:
  us_academy_words        — 300 curated academic words (Level 1-3)
  us_academy_word_progress — per-word 5-step learning progress + SM-2
  us_academy_passages     — CLEAR Corpus reading passages (filtered 3-4th grade)
  us_academy_sessions     — current learning session (level/unit/word index)
  us_academy_unit_results — unit test + mini quiz results
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, Text

from ._base import Base


class USAcademyWord(Base):
    """300개 학술 단어 — Merriam-Webster + WordNet 데이터 포함"""
    __tablename__ = "us_academy_words"

    id              = Column(Integer, primary_key=True)
    word            = Column(String, nullable=False, index=True)
    level           = Column(Integer, nullable=False, index=True)   # 1, 2, 3
    category        = Column(String, nullable=False)                # "thinking", "connecting", "text", "ela", "math", "science", "social"
    sort_order      = Column(Integer, default=0)                    # order within category

    # Merriam-Webster Elementary API data
    definition      = Column(Text)       # 영영 정의 (child-friendly)
    part_of_speech  = Column(String)     # noun, verb, adjective ...
    audio_url       = Column(String)     # MW 발음 오디오 URL
    example_1       = Column(Text)       # 교과 예문 1
    example_2       = Column(Text)       # 교과 예문 2 (다른 과목 맥락)

    # WordNet data
    synonyms_json   = Column(String)     # JSON list of synonyms
    antonyms_json   = Column(String)     # JSON list of antonyms

    # Manual curation
    morphology      = Column(String)     # e.g. "pre- (before) + dict (say)"
    word_family     = Column(String)     # e.g. "predict, prediction, predictable"

    is_active       = Column(Boolean, default=True)


class USAcademyWordProgress(Base):
    """단어별 5단계 학습 진행 + SM-2 간격반복"""
    __tablename__ = "us_academy_word_progress"

    id              = Column(Integer, primary_key=True)
    word_id         = Column(Integer, nullable=False, index=True)
    word            = Column(String, nullable=False)

    # 5-step completion flags
    step_meet_it    = Column(Boolean, default=False)   # ① 정의 읽기
    step_see_it     = Column(Boolean, default=False)   # ② 예문 읽기
    step_use_it     = Column(Boolean, default=False)   # ③ 빈칸 채우기
    step_know_it    = Column(Boolean, default=False)   # ④ 동의어/반의어 선택
    step_own_it     = Column(Boolean, default=False)   # ⑤ 올바른 사용 선택
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


class USAcademyPassage(Base):
    """CLEAR Corpus 기반 독해 지문 (Lexile 520L-820L, 200-400 words)"""
    __tablename__ = "us_academy_passages"

    id              = Column(Integer, primary_key=True)
    clear_id        = Column(String, index=True)       # CLEAR Corpus 원본 ID
    title           = Column(String)
    text            = Column(Text, nullable=False)
    genre           = Column(String)                   # "fiction" | "nonfiction"
    lexile          = Column(Integer)                  # Lexile score
    word_count      = Column(Integer)
    grade_level     = Column(Float)                    # 3.0 ~ 4.9

    # 연결된 단어 (해당 unit 단어가 지문에 등장)
    linked_words_json = Column(String)                 # JSON list of word IDs
    unit_level      = Column(Integer)                  # 1, 2, or 3
    unit_number     = Column(Integer)                  # 1-N within level

    # 이해 질문 (3개)
    q1_text         = Column(Text)                     # Main idea (객관식)
    q1_options_json = Column(String)                   # JSON list of 4 options
    q1_answer       = Column(String)                   # correct option key

    q2_text         = Column(Text)                     # Key detail (객관식)
    q2_options_json = Column(String)
    q2_answer       = Column(String)

    q3_text         = Column(Text)                     # Inference (단문 쓰기)

    is_active       = Column(Boolean, default=True)


class USAcademySession(Base):
    """현재 학습 세션 — 레벨/유닛/단어 인덱스 추적"""
    __tablename__ = "us_academy_sessions"

    id              = Column(Integer, primary_key=True)
    level           = Column(Integer, default=1)       # 1, 2, 3
    unit_number     = Column(Integer, default=1)       # 1-N
    word_index      = Column(Integer, default=0)       # 0-14 within unit
    current_step    = Column(String, default="MEET_IT") # MEET_IT / SEE_IT / USE_IT / KNOW_IT / OWN_IT / MINI_QUIZ / UNIT_TEST / READING
    started_date    = Column(String)
    last_active     = Column(String, index=True)
    is_completed    = Column(Boolean, default=False)


class USAcademyUnitResult(Base):
    """Mini Quiz / Unit Test / Reading 결과 기록"""
    __tablename__ = "us_academy_unit_results"

    id              = Column(Integer, primary_key=True)
    level           = Column(Integer)
    unit_number     = Column(Integer)
    result_type     = Column(String)   # "mini_quiz" | "unit_test" | "reading"
    score           = Column(Integer)  # correct count
    total           = Column(Integer)  # total questions
    passed          = Column(Boolean, default=False)
    wrong_words_json = Column(String)  # JSON list of wrong word IDs
    completed_at    = Column(String)


__all__ = [
    "USAcademyWord",
    "USAcademyWordProgress",
    "USAcademyPassage",
    "USAcademySession",
    "USAcademyUnitResult",
]
