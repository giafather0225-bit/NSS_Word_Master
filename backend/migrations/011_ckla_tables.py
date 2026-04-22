"""
migrations/011_ckla_tables.py — CKLA G3 통합 스키마 마이그레이션
Section: Academy
Dependencies: database.py
API: none (run directly)

New tables:
  us_academy_domains        — 11 CKLA 도메인
  us_academy_lessons        — 104 레슨 (지문 + Word Work)
  us_academy_questions      — 819 문제 (Literal/Inferential/Evaluative)
  us_academy_word_lesson    — 단어 ↔ 레슨 N:M 링크
  us_academy_lesson_progress — 레슨별 학습 진행 상태
  us_academy_question_responses — 문제별 답변 기록

Modified tables:
  us_academy_words     — ADD COLUMN: domain_num, lesson_num
  us_academy_sessions  — ADD COLUMN: domain_id, lesson_id, ckla_step

Idempotent — safe to run multiple times.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag ACADEMY @tag SYSTEM
def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 011] DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    # ── 새 테이블 ──────────────────────────────────────────────────────────────

    conn.executescript("""
        -- CKLA G3 도메인 (11개)
        CREATE TABLE IF NOT EXISTS us_academy_domains (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_num      INTEGER NOT NULL UNIQUE,   -- 1~11
            title           TEXT    NOT NULL,
            source_pdf      TEXT,
            lesson_count    INTEGER DEFAULT 0,
            is_active       INTEGER DEFAULT 1
        );

        -- CKLA 레슨 (104개) — 지문 + Word Work
        CREATE TABLE IF NOT EXISTS us_academy_lessons (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id       INTEGER NOT NULL REFERENCES us_academy_domains(id),
            domain_num      INTEGER NOT NULL,
            lesson_num      INTEGER NOT NULL,
            title           TEXT    NOT NULL,
            passage         TEXT    NOT NULL,           -- 원문 지문
            passage_chars   INTEGER DEFAULT 0,
            word_work_word  TEXT,                       -- 집중 단어 1개
            is_active       INTEGER DEFAULT 1,
            UNIQUE (domain_num, lesson_num)
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_lessons_domain
            ON us_academy_lessons (domain_id);

        -- 문제 (819개) — kind: Literal / Inferential / Evaluative
        CREATE TABLE IF NOT EXISTS us_academy_questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id       INTEGER NOT NULL REFERENCES us_academy_lessons(id),
            question_num    INTEGER NOT NULL,
            kind            TEXT    NOT NULL
                                CHECK (kind IN ('Literal','Inferential','Evaluative')),
            question_text   TEXT    NOT NULL,
            model_answer    TEXT,
            UNIQUE (lesson_id, question_num)
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_questions_lesson
            ON us_academy_questions (lesson_id);
        CREATE INDEX IF NOT EXISTS ix_us_academy_questions_kind
            ON us_academy_questions (kind);

        -- 단어 ↔ 레슨 N:M 링크
        -- (한 단어가 여러 레슨에 등장할 수 있고,
        --  한 레슨에 여러 단어가 있음)
        CREATE TABLE IF NOT EXISTS us_academy_word_lesson (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id         INTEGER NOT NULL REFERENCES us_academy_words(id),
            lesson_id       INTEGER NOT NULL REFERENCES us_academy_lessons(id),
            UNIQUE (word_id, lesson_id)
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_word_lesson_word
            ON us_academy_word_lesson (word_id);
        CREATE INDEX IF NOT EXISTS ix_us_academy_word_lesson_lesson
            ON us_academy_word_lesson (lesson_id);

        -- 레슨별 학습 진행 상태
        CREATE TABLE IF NOT EXISTS us_academy_lesson_progress (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id           INTEGER NOT NULL REFERENCES us_academy_lessons(id) UNIQUE,
            reading_done        INTEGER DEFAULT 0,          -- 지문 읽기 완료
            reading_done_at     TEXT,
            vocab_done          INTEGER DEFAULT 0,          -- 단어 확인 완료
            questions_attempted INTEGER DEFAULT 0,
            questions_correct   INTEGER DEFAULT 0,
            word_work_done      INTEGER DEFAULT 0,          -- Word Work 완료
            completed           INTEGER DEFAULT 0,          -- 레슨 전체 완료
            completed_at        TEXT,
            last_active         TEXT
        );

        -- 문제별 답변 기록 (AI 채점 포함)
        CREATE TABLE IF NOT EXISTS us_academy_question_responses (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id         INTEGER NOT NULL REFERENCES us_academy_questions(id),
            lesson_progress_id  INTEGER REFERENCES us_academy_lesson_progress(id),
            user_answer         TEXT,
            ai_score            INTEGER DEFAULT 0
                                    CHECK (ai_score BETWEEN 0 AND 2),
                                    -- 0: 틀림, 1: 부분 정답, 2: 정답
            ai_feedback         TEXT,
            needs_parent_review INTEGER DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_question_responses_question
            ON us_academy_question_responses (question_id);
        CREATE INDEX IF NOT EXISTS ix_us_academy_question_responses_review
            ON us_academy_question_responses (needs_parent_review);
    """)

    # ── 기존 테이블 컬럼 추가 (ADD COLUMN — 이미 있으면 무시) ────────────────

    existing_words_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(us_academy_words)")
    }
    if "domain_num" not in existing_words_cols:
        conn.execute("ALTER TABLE us_academy_words ADD COLUMN domain_num INTEGER")
        print("[migration 011] us_academy_words: domain_num 추가")
    if "lesson_num" not in existing_words_cols:
        conn.execute("ALTER TABLE us_academy_words ADD COLUMN lesson_num INTEGER")
        print("[migration 011] us_academy_words: lesson_num 추가")

    existing_sess_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(us_academy_sessions)")
    }
    if "domain_id" not in existing_sess_cols:
        conn.execute("ALTER TABLE us_academy_sessions ADD COLUMN domain_id INTEGER")
        print("[migration 011] us_academy_sessions: domain_id 추가")
    if "lesson_id" not in existing_sess_cols:
        conn.execute("ALTER TABLE us_academy_sessions ADD COLUMN lesson_id INTEGER")
        print("[migration 011] us_academy_sessions: lesson_id 추가")
    if "ckla_step" not in existing_sess_cols:
        # reading → vocab → questions → word_work → done
        conn.execute(
            "ALTER TABLE us_academy_sessions ADD COLUMN "
            "ckla_step TEXT DEFAULT 'reading'"
        )
        print("[migration 011] us_academy_sessions: ckla_step 추가")

    conn.commit()
    conn.close()
    print("[migration 011] CKLA 스키마 마이그레이션 완료.")


if __name__ == "__main__":
    migrate()
