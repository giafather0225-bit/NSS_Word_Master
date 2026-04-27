"""
migrations/014_report_schedule.py — Seed report schedule AppConfig keys
Section: System
Idempotent — safe to run repeatedly.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_DEFAULTS = [
    ("report_enabled",     "0"),
    ("report_day_of_week", "1"),
    ("report_child_name",  "Gia"),
]


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 014] DB not found at {DB_PATH}; skipping.")
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        added = []
        for key, val in _DEFAULTS:
            exists = conn.execute(
                "SELECT 1 FROM app_config WHERE key = ?", (key,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    (key, val),
                )
                added.append(key)
        conn.commit()
        if added:
            print(f"[migration 014] Seeded keys: {', '.join(added)}")
        else:
            print("[migration 014] All keys already present.")
    finally:
        conn.close()
    print("[migration 014] report_schedule complete.")


if __name__ == "__main__":
    migrate()
