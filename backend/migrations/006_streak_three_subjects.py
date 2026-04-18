"""
migrations/006_streak_three_subjects.py — Three-subject streak
Section: System
Dependencies: database.py
API: none (run directly)

Extends streak_logs with game_done and splits streak_condition into
streak_subjects (CSV) + streak_mode (all|any).
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# Mapping of legacy streak_condition → (subjects, mode).
_LEGACY_MAP = {
    "both":         ("english,math",       "all"),
    "either":       ("english,math",       "any"),
    "english_only": ("english",            "all"),
    "math_only":    ("math",               "all"),
}


# @tag SYSTEM @tag STREAK
def migrate():
    """Add game_done column + migrate streak_condition. Idempotent."""
    if not DB_PATH.exists():
        print(f"[migration 006] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    now = datetime.now().isoformat()

    # ── streak_logs.game_done ─────────────────────────────────
    cols = {row[1] for row in conn.execute("PRAGMA table_info(streak_logs)").fetchall()}
    if "game_done" not in cols:
        conn.execute("ALTER TABLE streak_logs ADD COLUMN game_done INTEGER DEFAULT 0")
        print("[migration 006] Added streak_logs.game_done")

    # ── Split streak_condition → streak_subjects + streak_mode ─
    have = {
        row[0]
        for row in conn.execute(
            "SELECT key FROM app_config WHERE key IN ('streak_subjects','streak_mode','streak_condition')"
        ).fetchall()
    }

    subjects, mode = "english,math", "all"  # default: game is optional (parent can enable)
    if "streak_condition" in have:
        legacy = conn.execute(
            "SELECT value FROM app_config WHERE key = 'streak_condition'"
        ).fetchone()
        if legacy and legacy[0] in _LEGACY_MAP:
            subjects, mode = _LEGACY_MAP[legacy[0]]

    if "streak_subjects" not in have:
        conn.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            ("streak_subjects", subjects, now),
        )
        print(f"[migration 006] Added streak_subjects = '{subjects}'")
    if "streak_mode" not in have:
        conn.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            ("streak_mode", mode, now),
        )
        print(f"[migration 006] Added streak_mode = '{mode}'")

    conn.commit()
    conn.close()
    print("[migration 006] Done.")


if __name__ == "__main__":
    migrate()
