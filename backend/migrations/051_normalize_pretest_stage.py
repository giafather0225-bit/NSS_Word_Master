"""
migrations/051_normalize_pretest_stage.py — Normalize math_progress stage "pretest" → "pre_test"
Section: Math
Idempotent — safe to run repeatedly.

Renames the legacy stage value "pretest" to "pre_test" in math_progress,
so the stage column has a single canonical spelling throughout the codebase.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE math_progress SET stage = 'pre_test' WHERE stage = 'pretest'"
        )
        updated = cur.rowcount
        conn.commit()
        print(f"[051] Normalized {updated} math_progress row(s): 'pretest' → 'pre_test'")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
