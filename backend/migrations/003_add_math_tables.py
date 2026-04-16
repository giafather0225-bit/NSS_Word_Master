"""
migrations/003_add_math_tables.py — Math section DB migration
Section: System
Dependencies: database.py, models.py (Math models)
API: none (run directly)

Creates 8 new Math tables and adds math_done column to streak_logs.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag SYSTEM @tag MATH
def migrate():
    """Create Math tables and extend streak_logs. Safe to run multiple times."""
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))

    # ── Create Math tables via SQLAlchemy models ──
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from backend.database import engine, Base
    import backend.models  # noqa: F401
    Base.metadata.create_all(engine, checkfirst=True)
    print("[migration] Ensured all Math tables exist.")

    # ── Extend streak_logs with math_done column ──
    cols = {row[1] for row in conn.execute("PRAGMA table_info(streak_logs)").fetchall()}
    if "math_done" not in cols:
        conn.execute("ALTER TABLE streak_logs ADD COLUMN math_done INTEGER DEFAULT 0")
        print("[migration] Added streak_logs.math_done")

    # ── Add streak_condition to app_config if not present ──
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'streak_condition'"
    ).fetchone()
    if not row:
        from datetime import datetime
        conn.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, ?)",
            ("streak_condition", "both", datetime.now().isoformat()),
        )
        print("[migration] Added streak_condition = 'both' to app_config")

    # ── Seed Math task settings ──
    existing = {
        row[0]
        for row in conn.execute("SELECT task_key FROM task_settings").fetchall()
    }
    math_tasks = [
        ("math_daily_challenge", False, 5, True),
        ("math_fact_fluency", False, 3, True),
        ("math_academy", False, 10, True),
    ]
    for key, req, xp, active in math_tasks:
        if key not in existing:
            conn.execute(
                "INSERT INTO task_settings (task_key, is_required, xp_value, is_active) VALUES (?, ?, ?, ?)",
                (key, int(req), xp, int(active)),
            )
            print(f"[migration] Seeded task_setting: {key}")

    conn.commit()
    conn.close()
    print("[migration] 003_add_math_tables complete.")


if __name__ == "__main__":
    migrate()
