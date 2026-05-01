"""
migrations/019_ckla_grade.py — CKLA grade-aware columns + XPLog source
Section: CKLA
Idempotent — safe to run repeatedly.

Changes:
  us_academy_domains        — ADD grade INTEGER NOT NULL DEFAULT 3
  us_academy_lessons        — ADD grade INTEGER NOT NULL DEFAULT 3
  us_academy_lesson_progress — ADD grade, started_at, difficulty_rating
  xp_logs                   — ADD source TEXT
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def _add_column(conn: sqlite3.Connection, table: str, col: str, definition: str) -> bool:
    """Add a column if not present. Returns True if added, False if already present."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if col in existing:
        return False
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
    return True


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 019] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        added: list[str] = []

        # us_academy_domains — grade
        if _add_column(conn, "us_academy_domains", "grade", "INTEGER NOT NULL DEFAULT 3"):
            added.append("us_academy_domains.grade")

        # us_academy_lessons — grade
        if _add_column(conn, "us_academy_lessons", "grade", "INTEGER NOT NULL DEFAULT 3"):
            added.append("us_academy_lessons.grade")

        # us_academy_lesson_progress — grade, started_at, difficulty_rating
        if _add_column(conn, "us_academy_lesson_progress", "grade", "INTEGER NOT NULL DEFAULT 3"):
            added.append("us_academy_lesson_progress.grade")
        if _add_column(conn, "us_academy_lesson_progress", "started_at", "TEXT"):
            added.append("us_academy_lesson_progress.started_at")
        if _add_column(conn, "us_academy_lesson_progress", "difficulty_rating", "TEXT"):
            added.append("us_academy_lesson_progress.difficulty_rating")

        # xp_logs — source
        if _add_column(conn, "xp_logs", "source", "TEXT"):
            added.append("xp_logs.source")

        # streak_logs — ckla_done
        if _add_column(conn, "streak_logs", "ckla_done", "BOOLEAN DEFAULT FALSE"):
            added.append("streak_logs.ckla_done")

        if added:
            conn.commit()
            for col in added:
                print(f"[migration 019] Added {col}")
        else:
            print("[migration 019] All columns already present — skipping.")

    finally:
        conn.close()

    print("[migration 019] complete.")


if __name__ == "__main__":
    migrate()
