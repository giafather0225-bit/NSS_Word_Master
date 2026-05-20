"""
Migration 063 — Streak Freeze: table + shop seed

Adds the Daily Streak Freeze feature — a Lumi-consumable item the child
can buy from the Reward Shop and burn on a day they miss study, keeping
their streak alive without parent involvement (vs Day-Off which requires
parental approval).

Schema:
  streak_freezes(used_date PK)       — one freeze per calendar day
  + UNIQUE on used_date so the same day can't be frozen twice
  + a 'streak_freeze' shop item seeded with price 50 Lumi

Idempotent:
  CREATE TABLE / INDEX / shop INSERT all use IF NOT EXISTS / OR IGNORE.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS streak_freezes (
                id           INTEGER PRIMARY KEY,
                used_date    TEXT NOT NULL,
                used_at      TEXT NOT NULL DEFAULT (datetime('now')),
                inventory_id INTEGER
            )
        """)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_streak_freezes_used_date "
            "ON streak_freezes(used_date)"
        )

        # Seed the shop item. INSERT OR IGNORE keyed on `name` would be ideal
        # but island_shop_items.name has no UNIQUE — fall back to a guarded
        # INSERT that checks first.
        existing = conn.execute(
            "SELECT id FROM island_shop_items WHERE name = ?",
            ("Streak Shield",),
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO island_shop_items
                    (name, category, sub_category, zone, price,
                     is_legend_currency, image, is_active, description)
                VALUES
                    ('Streak Shield', 'streak_freeze', 'special', 'all', 50,
                     0, '/static/img/island/streak_shield.png', 1,
                     'Use today to keep your streak alive without studying. One per day.')
            """)

        conn.commit()
        print("063: streak_freezes table + Streak Shield shop item ready")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
