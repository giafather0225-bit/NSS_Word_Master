"""
migrations/016_weekly_goals.py — Create weekly_goals table
Section: Parent
Idempotent — safe to run repeatedly.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_DDL = """
CREATE TABLE IF NOT EXISTS weekly_goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT    NOT NULL UNIQUE,
    label       TEXT    NOT NULL,
    target      INTEGER NOT NULL DEFAULT 0,
    is_active   INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

_DEFAULTS = [
    ("words_correct", "Words Mastered",   20),
    ("xp_earned",     "XP Earned",       100),
    ("streak_days",   "Streak Days",       5),
    ("study_minutes", "Study Minutes",    60),
]


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 016] DB not found at {DB_PATH}; skipping.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(_DDL)
        conn.commit()
        added = []
        for key, label, target in _DEFAULTS:
            exists = conn.execute(
                "SELECT 1 FROM weekly_goals WHERE key = ?", (key,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO weekly_goals (key, label, target, is_active) VALUES (?, ?, ?, 1)",
                    (key, label, target),
                )
                added.append(key)
        conn.commit()
        if added:
            print(f"[migration 016] Seeded goals: {', '.join(added)}")
        else:
            print("[migration 016] All goals already present.")
    finally:
        conn.close()
    print("[migration 016] weekly_goals complete.")


if __name__ == "__main__":
    migrate()
