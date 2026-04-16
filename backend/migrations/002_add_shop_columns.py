"""
migrations/002_add_shop_columns.py — Add description, category to reward_items
and is_equipped to purchased_rewards.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def migrate():
    """Add missing columns if they don't already exist."""
    if not DB_PATH.exists():
        print(f"[migration] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))

    # Get existing columns for reward_items
    cols_ri = {row[1] for row in conn.execute("PRAGMA table_info(reward_items)").fetchall()}
    if "description" not in cols_ri:
        conn.execute("ALTER TABLE reward_items ADD COLUMN description TEXT DEFAULT ''")
        print("[migration] Added reward_items.description")
    if "category" not in cols_ri:
        conn.execute("ALTER TABLE reward_items ADD COLUMN category TEXT DEFAULT 'badge'")
        print("[migration] Added reward_items.category")

    # Get existing columns for purchased_rewards
    cols_pr = {row[1] for row in conn.execute("PRAGMA table_info(purchased_rewards)").fetchall()}
    if "is_equipped" not in cols_pr:
        conn.execute("ALTER TABLE purchased_rewards ADD COLUMN is_equipped INTEGER DEFAULT 0")
        print("[migration] Added purchased_rewards.is_equipped")

    conn.commit()
    conn.close()
    print("[migration] 002_add_shop_columns complete.")


if __name__ == "__main__":
    migrate()
