"""
033_add_qa_done.py — Add qa_done column to us_academy_lesson_progress.

Lesson completion now requires 4 tabs: Read + Words + Q&A + Word Work.
Previously only 3 tabs were tracked (reading + vocab + word_work).

Idempotent: uses ALTER TABLE only when the column is absent.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(us_academy_lesson_progress)")
    cols = {row[1] for row in cur.fetchall()}

    if "qa_done" not in cols:
        cur.execute(
            "ALTER TABLE us_academy_lesson_progress ADD COLUMN qa_done BOOLEAN DEFAULT 0"
        )
        conn.commit()
        print("[033] qa_done column added to us_academy_lesson_progress")
    else:
        print("[033] qa_done column already exists — skipped")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    try:
        run(conn)
    finally:
        conn.close()
