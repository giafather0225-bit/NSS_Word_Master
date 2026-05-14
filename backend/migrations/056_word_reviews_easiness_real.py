"""
migrations/056_word_reviews_easiness_real.py — Convert word_reviews.easiness to REAL.

word_reviews.easiness was created as TEXT (default '2.5') by migration 004.
SM-2 code stored str(round(ease, 2)) and read float(ease) on every review
cycle, and get_review_stats' ORDER BY easiness did a lexical string sort
instead of a numeric one — so "struggling words" could be mis-ranked.

SQLite cannot ALTER a column's declared type, so we rebuild the table with
easiness REAL, CASTing existing string values. Idempotent: skipped when the
easiness column is already declared REAL.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def _easiness_type(conn) -> str:
    """Return the declared type of word_reviews.easiness (upper-cased)."""
    for row in conn.execute("PRAGMA table_info(word_reviews)").fetchall():
        # row = (cid, name, type, notnull, dflt_value, pk)
        if row[1] == "easiness":
            return (row[2] or "").upper()
    return ""


def _rebuild_word_reviews_real(conn) -> None:
    """Recreate word_reviews with easiness REAL, preserving all data."""
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.executescript("""
        CREATE TABLE word_reviews_new (
            id            INTEGER PRIMARY KEY,
            study_item_id INTEGER REFERENCES study_items(id),
            word          TEXT,
            subject       TEXT DEFAULT 'English',
            textbook      TEXT DEFAULT '',
            lesson        TEXT DEFAULT '',
            easiness      REAL DEFAULT 2.5,
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
             total_reviews, total_correct, source, question, hint, source_ref)
        SELECT id, study_item_id, word, subject, textbook, lesson,
               CAST(easiness AS REAL), interval, repetitions, next_review, last_review,
               total_reviews, total_correct, source, question, hint, source_ref
        FROM word_reviews;
        DROP TABLE word_reviews;
        ALTER TABLE word_reviews_new RENAME TO word_reviews;
        CREATE INDEX IF NOT EXISTS ix_word_reviews_word            ON word_reviews(word);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_study_item_id   ON word_reviews(study_item_id);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_next_review     ON word_reviews(next_review);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_subject_textbook ON word_reviews(subject, textbook);
        CREATE INDEX IF NOT EXISTS ix_word_reviews_source          ON word_reviews(source);
    """)
    conn.execute("PRAGMA foreign_keys=ON")


def run(db_path: Path = DB_PATH) -> None:
    if not Path(db_path).exists():
        print(f"056: DB not found at {db_path}; skipping.")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "word_reviews" not in tables:
            print("056: word_reviews table absent; skipping.")
            return
        if _easiness_type(conn) == "REAL":
            print("056: word_reviews.easiness already REAL; skipping.")
            return

        _rebuild_word_reviews_real(conn)
        conn.commit()
        print("056: word_reviews.easiness converted TEXT -> REAL")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
