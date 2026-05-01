"""
migrations/020_ckla_badges.py — CKLA badge catalog + user badge tables
Section: CKLA
Idempotent — safe to run repeatedly.

Creates:
  ckla_badges      — badge catalog (domain complete + grade master)
  ckla_user_badges — user earned badges (UNIQUE on badge_key)

Seeds 12 badges:
  domain_1_complete … domain_11_complete  (condition_type=domain_complete)
  grade_3_master                           (condition_type=grade_complete)
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_CREATE_BADGES = """
CREATE TABLE IF NOT EXISTS ckla_badges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_key       TEXT    NOT NULL UNIQUE,
    badge_name      TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    condition_type  TEXT    NOT NULL,
    condition_value INTEGER NOT NULL,
    image_path      TEXT,
    created_at      TEXT    NOT NULL
)
"""

_CREATE_USER_BADGES = """
CREATE TABLE IF NOT EXISTS ckla_user_badges (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_key  TEXT    NOT NULL UNIQUE,
    earned_at  TEXT    NOT NULL
)
"""

_SEED_BADGES = [
    ("domain_1_complete",  "Explorer",       "Complete all lessons in Domain 1",             "domain_complete",  1),
    ("domain_2_complete",  "Historian",      "Complete all lessons in Domain 2",             "domain_complete",  2),
    ("domain_3_complete",  "Scientist",      "Complete all lessons in Domain 3",             "domain_complete",  3),
    ("domain_4_complete",  "Naturalist",     "Complete all lessons in Domain 4",             "domain_complete",  4),
    ("domain_5_complete",  "Geographer",     "Complete all lessons in Domain 5",             "domain_complete",  5),
    ("domain_6_complete",  "Inventor",       "Complete all lessons in Domain 6",             "domain_complete",  6),
    ("domain_7_complete",  "Narrator",       "Complete all lessons in Domain 7",             "domain_complete",  7),
    ("domain_8_complete",  "Anthropologist", "Complete all lessons in Domain 8",             "domain_complete",  8),
    ("domain_9_complete",  "Ecologist",      "Complete all lessons in Domain 9",             "domain_complete",  9),
    ("domain_10_complete", "Astronomer",     "Complete all lessons in Domain 10",            "domain_complete", 10),
    ("domain_11_complete", "Champion",       "Complete all lessons in Domain 11",            "domain_complete", 11),
    ("grade_3_master",     "Grade 3 Master", "Complete all 11 domains in Grade 3",          "grade_complete",   3),
]


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 020] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}

        created: list[str] = []

        if "ckla_badges" not in tables:
            conn.execute(_CREATE_BADGES)
            created.append("ckla_badges")

        if "ckla_user_badges" not in tables:
            conn.execute(_CREATE_USER_BADGES)
            created.append("ckla_user_badges")

        if created:
            conn.commit()
            for t in created:
                print(f"[migration 020] Created table {t}")
        else:
            print("[migration 020] Tables already present — checking seed data.")

        # Seed badges (INSERT OR IGNORE — idempotent)
        now = datetime.now().isoformat()
        seeded = 0
        for badge_key, name, desc, ctype, cval in _SEED_BADGES:
            cur = conn.execute(
                "INSERT OR IGNORE INTO ckla_badges "
                "(badge_key, badge_name, description, condition_type, condition_value, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (badge_key, name, desc, ctype, cval, now),
            )
            seeded += cur.rowcount

        conn.commit()
        if seeded:
            print(f"[migration 020] Seeded {seeded} badge(s).")
        else:
            print("[migration 020] Badge seeds already present.")

    finally:
        conn.close()

    print("[migration 020] complete.")


if __name__ == "__main__":
    migrate()
