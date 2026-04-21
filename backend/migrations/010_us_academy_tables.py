"""
migrations/010_us_academy_tables.py — US Academy (미국학교 대비) 테이블 생성
Section: Academy
Dependencies: database.py
API: none (run directly)

Creates:
  us_academy_words
  us_academy_word_progress
  us_academy_passages
  us_academy_sessions
  us_academy_unit_results

Idempotent — safe to run multiple times.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag ACADEMY @tag SYSTEM
def migrate() -> None:
    """Create US Academy tables if they don't exist."""
    if not DB_PATH.exists():
        print(f"[migration 010] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS us_academy_words (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            word            TEXT NOT NULL,
            level           INTEGER NOT NULL,
            category        TEXT NOT NULL,
            sort_order      INTEGER DEFAULT 0,
            definition      TEXT,
            part_of_speech  TEXT,
            audio_url       TEXT,
            example_1       TEXT,
            example_2       TEXT,
            synonyms_json   TEXT,
            antonyms_json   TEXT,
            morphology      TEXT,
            word_family     TEXT,
            is_active       INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_words_word
            ON us_academy_words (word);
        CREATE INDEX IF NOT EXISTS ix_us_academy_words_level
            ON us_academy_words (level);

        CREATE TABLE IF NOT EXISTS us_academy_word_progress (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id         INTEGER NOT NULL,
            word            TEXT NOT NULL,
            step_meet_it    INTEGER DEFAULT 0,
            step_see_it     INTEGER DEFAULT 0,
            step_use_it     INTEGER DEFAULT 0,
            step_know_it    INTEGER DEFAULT 0,
            step_own_it     INTEGER DEFAULT 0,
            steps_completed INTEGER DEFAULT 0,
            sm2_repetitions INTEGER DEFAULT 0,
            sm2_easiness    REAL DEFAULT 2.5,
            sm2_interval    INTEGER DEFAULT 1,
            next_review     TEXT,
            correct_count   INTEGER DEFAULT 0,
            wrong_count     INTEGER DEFAULT 0,
            last_studied    TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_word_progress_word_id
            ON us_academy_word_progress (word_id);
        CREATE INDEX IF NOT EXISTS ix_us_academy_word_progress_next_review
            ON us_academy_word_progress (next_review);

        CREATE TABLE IF NOT EXISTS us_academy_passages (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            clear_id            TEXT,
            title               TEXT,
            text                TEXT NOT NULL,
            genre               TEXT,
            lexile              INTEGER,
            word_count          INTEGER,
            grade_level         REAL,
            linked_words_json   TEXT,
            unit_level          INTEGER,
            unit_number         INTEGER,
            q1_text             TEXT,
            q1_options_json     TEXT,
            q1_answer           TEXT,
            q2_text             TEXT,
            q2_options_json     TEXT,
            q2_answer           TEXT,
            q3_text             TEXT,
            is_active           INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_passages_clear_id
            ON us_academy_passages (clear_id);

        CREATE TABLE IF NOT EXISTS us_academy_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            level           INTEGER DEFAULT 1,
            unit_number     INTEGER DEFAULT 1,
            word_index      INTEGER DEFAULT 0,
            current_step    TEXT DEFAULT 'MEET_IT',
            started_date    TEXT,
            last_active     TEXT,
            is_completed    INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS ix_us_academy_sessions_last_active
            ON us_academy_sessions (last_active);

        CREATE TABLE IF NOT EXISTS us_academy_unit_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            level           INTEGER,
            unit_number     INTEGER,
            result_type     TEXT,
            score           INTEGER,
            total           INTEGER,
            passed          INTEGER DEFAULT 0,
            wrong_words_json TEXT,
            completed_at    TEXT
        );
    """)

    conn.commit()
    conn.close()
    print("[migration 010] US Academy tables created (or already existed).")


if __name__ == "__main__":
    migrate()
