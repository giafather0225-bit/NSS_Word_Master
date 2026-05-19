"""
Migration 062 — Drop the legacy `rewards` table

Background: the `rewards` table backed the original parent-managed reward
list (`backend/routers/rewards.py`). It was superseded by the XP-based
reward shop (`reward_shop.py`, `reward_items`, `purchased_rewards`).

State at removal:
  - 0 rows in production DB (verified 2026-05-19)
  - 0 frontend callers (the only reference was an outdated header comment
    in child.js — also removed in the same change)
  - 0 backend callers (rewards router + Reward model deleted)

Idempotent: DROP TABLE IF EXISTS.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS rewards")
        conn.commit()
        print("062: rewards table dropped (or was already absent)")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
