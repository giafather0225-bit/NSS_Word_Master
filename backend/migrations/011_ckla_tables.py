"""
migrations/011_ckla_tables.py — CKLA G3 unified schema migration
Section: Academy
Dependencies: database.py
API: none (run directly)

New tables:
  us_academy_domains        — 11 CKLA domains
  us_academy_lessons        — 104 lessons (passage + Word Work)
  us_academy_questions      — 819 questions (Literal/Inferential/Evaluative)
  us_academy_word_lesson    — word ↔ lesson N:M link
  us_academy_lesson_progress — per-lesson study progress
  us_academy_question_responses — per-question answer records

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

    # ── New tables ──────────────────────────────────────────────────────────────

    conn.executescript("""
        -- CKLA G3 domains (11)
        CREATE TABLE IF NOT EXISTS us_academy_domains (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_num      INTEGER NOT NULL UNIQUE,   -- 1~11
            title           TEXT    NOT NULL,
            source_pdf      TEXT,
            lesson_count    INTEGER DEFAULT 0,
            is_active       INTEGER DEFAULT 1
        );

        -- CKLA lessons (104) — passage + Word Work
        CREATE TABLE IF NOT EXISTS us_academy_lessons (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id       INTEGER NOT NULL REFERENCES us_academy_domains(id),
            domain_num      INTEGER NOT NULL,
            lesson_num      INTEGER NOT NULL,
            title           TEXT    NOT NULL,
            passage         TEXT    NOT NULL,           -- original passage
            passage_chars   INTEGER DEFAULT 0,
            word_work_word  TEXT,                       -- single focus word
            is_active       INTEGER DEFAULT 1,
            UNIQUE (domain_num, lesson_num)
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_lessons_domain
            ON us_academy_lessons (domain_id);

        -- Questions (819) — kind: Literal / Inferential / Evaluative
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

        -- word ↔ lesson N:M link
        -- (one word can appear in many lessons, and
        --  one lesson has many words)
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

        -- per-lesson study progress
        CREATE TABLE IF NOT EXISTS us_academy_lesson_progress (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id           INTEGER NOT NULL REFERENCES us_academy_lessons(id) UNIQUE,
            reading_done        INTEGER DEFAULT 0,          -- passage reading done
            reading_done_at     TEXT,
            vocab_done          INTEGER DEFAULT 0,          -- vocab check done
            questions_attempted INTEGER DEFAULT 0,
            questions_correct   INTEGER DEFAULT 0,
            word_work_done      INTEGER DEFAULT 0,          -- Word Work done
            completed           INTEGER DEFAULT 0,          -- whole lesson done
            completed_at        TEXT,
            last_active         TEXT
        );

        -- per-question answer records (incl. AI grading)
        CREATE TABLE IF NOT EXISTS us_academy_question_responses (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id         INTEGER NOT NULL REFERENCES us_academy_questions(id),
            lesson_progress_id  INTEGER REFERENCES us_academy_lesson_progress(id),
            user_answer         TEXT,
            ai_score            INTEGER DEFAULT 0
                                    CHECK (ai_score BETWEEN 0 AND 2),
                                    -- 0: wrong, 1: partial, 2: correct
            ai_feedback         TEXT,
            needs_parent_review INTEGER DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_question_responses_question
            ON us_academy_question_responses (question_id);
        CREATE INDEX IF NOT EXISTS ix_us_academy_question_responses_review
            ON us_academy_question_responses (needs_parent_review);
    """)

    # ── Add columns to existing tables (ADD COLUMN — skip if already present) ──

    existing_words_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(us_academy_words)")
    }
    if "domain_num" not in existing_words_cols:
        conn.execute("ALTER TABLE us_academy_words ADD COLUMN domain_num INTEGER")
        print("[migration 011] us_academy_words: added domain_num")
    if "lesson_num" not in existing_words_cols:
        conn.execute("ALTER TABLE us_academy_words ADD COLUMN lesson_num INTEGER")
        print("[migration 011] us_academy_words: added lesson_num")

    existing_sess_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(us_academy_sessions)")
    }
    if "domain_id" not in existing_sess_cols:
        conn.execute("ALTER TABLE us_academy_sessions ADD COLUMN domain_id INTEGER")
        print("[migration 011] us_academy_sessions: added domain_id")
    if "lesson_id" not in existing_sess_cols:
        conn.execute("ALTER TABLE us_academy_sessions ADD COLUMN lesson_id INTEGER")
        print("[migration 011] us_academy_sessions: added lesson_id")
    if "ckla_step" not in existing_sess_cols:
        # reading → vocab → questions → word_work → done
        conn.execute(
            "ALTER TABLE us_academy_sessions ADD COLUMN "
            "ckla_step TEXT DEFAULT 'reading'"
        )
        print("[migration 011] us_academy_sessions: added ckla_step")

    conn.commit()
    conn.close()
    print("[migration 011] CKLA schema migration complete.")


if __name__ == "__main__":
    migrate()
