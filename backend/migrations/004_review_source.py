"""
migrations/004_review_source.py — Unified Review source support.

Adds WordReview columns so Daily Words and My Words can join the SM-2 queue
alongside Academy:
  - source         TEXT    ('academy' | 'daily' | 'my')  default 'academy'
  - question       TEXT    meaning (was read from StudyItem)
  - hint           TEXT    example sentence
  - source_ref     TEXT    free-form origin id (e.g. grade_3/week_2 or list name)

Also relaxes word_reviews.study_item_id to allow NULL for non-Academy rows.
SQLite cannot ALTER a column's NOT NULL directly, so we rebuild the table
only if the current schema has NOT NULL on study_item_id.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def _col_notnull(conn, table: str, col: str) -> bool:
    for row in conn.execute(f"PRAGMA table_info({table})").fetchall():
        # row = (cid, name, type, notnull, dflt_value, pk)
        if row[1] == col:
            return bool(row[3])
    return False


def _rebuild_word_reviews_nullable(conn) -> None:
    """Recreate word_reviews with study_item_id NULLABLE, preserving data."""
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.executescript("""
        CREATE TABLE word_reviews_new (
            id            INTEGER PRIMARY KEY,
            study_item_id INTEGER REFERENCES study_items(id),
            word          TEXT,
            subject       TEXT DEFAULT 'English',
            textbook      TEXT DEFAULT '',
            lesson        TEXT DEFAULT '',
            easiness      TEXT DEFAULT '2.5',
            interval      INTEGER DEFAULT 0,
            repetitions   INTEGER DEFAULT 0,
            next_review   TEXT,
            last_review   TEXT DEFAULT '',
            total_reviews INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            source        TEXT DEFAULT 'academy',
            question      TEXT DEFAULT '',
            hint          TEXT DEFAULT '',
            source_ref    TEXT DEFAULT ''
        );
        INSERT INTO word_reviews_new
            (id, study_item_id, word, subject, textbook, lesson,
             easiness, interval, repetitions, next_review, last_review,
             total_reviews, total_correct)
        SELECT id, study_item_id, word, subject, textbook, lesson,
               easiness, interval, repetitions, next_review, last_review,
               total_reviews, total_correct
        FROM word_reviews;
        DROP TABLE word_reviews;
        ALTER TABLE word_reviews_new RENAME TO word_reviews;
        CREATE INDEX IF NOT EXISTS ix_word_reviews_word         ON word_reviews(word);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_study_item_id ON word_reviews(study_item_id);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_next_review  ON word_reviews(next_review);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_subject_textbook ON word_reviews(subject, textbook);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_source       ON word_reviews(source);
    """)
    conn.execute("PRAGMA foreign_keys=ON")


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))

    needs_rebuild = _col_notnull(conn, "word_reviews", "study_item_id")
    existing = {row[1] for row in conn.execute("PRAGMA table_info(word_reviews)").fetchall()}

    if needs_rebuild:
        _rebuild_word_reviews_nullable(conn)
        print("[migration] Rebuilt word_reviews: study_item_id nullable + new columns added.")
    else:
        for col, ddl in (
            ("source",     "ALTER TABLE word_reviews ADD COLUMN source TEXT DEFAULT 'academy'"),
            ("question",   "ALTER TABLE word_reviews ADD COLUMN question TEXT DEFAULT ''"),
            ("hint",       "ALTER TABLE word_reviews ADD COLUMN hint TEXT DEFAULT ''"),
            ("source_ref", "ALTER TABLE word_reviews ADD COLUMN source_ref TEXT DEFAULT ''"),
        ):
            if col not in existing:
                conn.execute(ddl)
                print(f"[migration] Added word_reviews.{col}")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_word_reviews_source ON word_reviews(source)")

    # Backfill: existing rows → source='academy'
    conn.execute("UPDATE word_reviews SET source='academy' WHERE source IS NULL OR source=''")

    conn.commit()
    conn.close()
    print("[migration] 004_review_source complete.")


if __name__ == "__main__":
    migrate()
