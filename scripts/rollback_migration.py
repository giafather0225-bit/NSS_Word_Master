"""
scripts/rollback_migration.py — Drop tables added by a specific migration
Section: System
Dependencies: backend/database.py, backend/migrations/
Usage:
  python scripts/rollback_migration.py --list
  python scripts/rollback_migration.py 022
  python scripts/rollback_migration.py 022 --dry-run
  python scripts/rollback_migration.py 022 --force
"""

import argparse
import sys
import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.database import DB_PATH, engine  # noqa: E402

BACKUP_DIR = Path.home() / "NSS_Learning" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

MIGRATION_DIR = ROOT / "backend" / "migrations"

# ── Migration table registry ──────────────────────────────────────
# Maps migration number → tables it created.
# Only tracks ADDITIVE migrations (DROP is not applicable to column-only changes).
# Update this dict when adding new migrations that create tables.
MIGRATION_TABLES: dict[str, list[str]] = {
    "001": [
        "app_config", "xp_logs", "streak_logs", "task_settings",
        "reward_items", "purchased_rewards", "daily_words_progress",
        "diary_entries", "growth_events", "day_off_requests",
        "academy_sessions", "learning_logs", "word_attempts",
        "academy_schedules", "growth_theme_progress",
    ],
    "002": [],   # Column additions only — not rollbackable via DROP TABLE
    "003": [
        "math_placement_results", "math_problems", "math_progress",
        "math_attempts", "math_wrong_review", "math_fact_fluency",
        "math_daily_challenges", "math_kangaroo_progress",
    ],
    "004": [],   # Column addition only
    "005": [],   # Column addition only
    "006": [],   # Column addition only
    "007": ["free_writings"],
    "008": [],   # Column addition only
    "009": [],   # Column addition only
    "010": [
        "us_academy_words", "us_academy_word_progress",
        "us_academy_passages", "us_academy_sessions", "us_academy_unit_results",
    ],
    "011": [
        "ckla_domains", "ckla_lessons", "ckla_questions",
        "ckla_word_lessons", "ckla_lesson_progress", "ckla_question_responses",
    ],
    "012": [],   # Column rename only
    "013": [],   # Column additions only
    "014": [],   # Column additions only
    "015": [],   # Column addition only
    "016": ["weekly_goals"],
    "017": [],   # UNIQUE index addition only
    "018": [
        "island_characters", "island_character_progress", "island_care_log",
        "island_shop_items", "island_inventory", "island_placed_items",
        "island_currency", "island_lumi_log", "island_legend_progress",
        "island_zone_status",
    ],
    "019": [],   # Column addition only (ckla_lessons.grade, xp_logs.source)
    "020": ["ckla_badges", "ckla_user_badges"],
    "021": ["ckla_spelling_grammar"],
    "022": [
        "math_spaced_review", "math_unit_tests", "math_placement_tests",
    ],
    "023": [],   # Column additions to island_shop_items
    "024": [],   # Column additions to island tables (decor extension)
}


# ── Helpers ───────────────────────────────────────────────────────
def list_migrations() -> None:
    """Print all known migrations with their table targets."""
    print("\nKnown migrations:\n")
    print(f"  {'No.':<6}  {'File':<40}  Tables created")
    print(f"  {'---':<6}  {'----':<40}  --------------")
    for num in sorted(MIGRATION_TABLES.keys()):
        tables = MIGRATION_TABLES[num]
        filepath = next(MIGRATION_DIR.glob(f"{num}_*.py"), None)
        fname = filepath.name if filepath else f"{num}_?.py  (file not found)"
        table_str = ", ".join(tables) if tables else "(column changes only)"
        print(f"  {num:<6}  {fname:<40}  {table_str}")
    print()


def get_existing_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    ).fetchall()
    return {r[0] for r in rows}


def make_safety_copy() -> Path:
    """Copy live DB to backups/voca_pre-rollback_<timestamp>.db."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"voca_pre-rollback_{ts}.db"
    import shutil
    shutil.copy2(DB_PATH, dest)
    return dest


# ── Main ──────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drop tables introduced by a specific migration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/rollback_migration.py --list
  python scripts/rollback_migration.py 022 --dry-run
  python scripts/rollback_migration.py 022
  python scripts/rollback_migration.py 022 --force
        """,
    )
    parser.add_argument(
        "migration", nargs="?",
        help="Migration number to roll back (e.g. 022)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List all known migrations and exit",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be dropped without actually doing it",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    if args.list:
        list_migrations()
        return

    if not args.migration:
        parser.print_help()
        sys.exit(1)

    # Normalize number
    num = args.migration.zfill(3)
    if num not in MIGRATION_TABLES:
        print(f"ERROR: Migration '{num}' not in registry. Run --list to see known migrations.")
        sys.exit(1)

    tables_to_drop = MIGRATION_TABLES[num]

    if not tables_to_drop:
        print(f"\nMigration {num} contains only column changes — no tables to drop.")
        print("Column-level rollback requires manual SQL. Example:")
        print("  sqlite3 ~/NSS_Learning/database/voca.db")
        print("  > ALTER TABLE <table> DROP COLUMN <column>;  -- SQLite 3.35+")
        sys.exit(0)

    # Connect and check which tables actually exist
    conn = sqlite3.connect(str(DB_PATH))
    existing = get_existing_tables(conn)
    conn.close()

    present     = [t for t in tables_to_drop if t in existing]
    not_present = [t for t in tables_to_drop if t not in existing]

    print(f"\nRollback migration {num}")
    print(f"  DB: {DB_PATH}\n")

    if not_present:
        print(f"  Already absent (skip): {', '.join(not_present)}")

    if not present:
        print("  Nothing to drop — all target tables already absent.")
        return

    print(f"  Tables to DROP: {', '.join(present)}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # Confirm
    if not args.force:
        print()
        answer = input(
            f"  This will DROP {len(present)} table(s). Type YES to confirm: "
        ).strip()
        if answer != "YES":
            print("Aborted.")
            return

    # Safety copy
    print("\nCreating safety copy before rollback...")
    safety = make_safety_copy()
    print(f"  Safety copy: {safety}")

    # Drop tables
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("PRAGMA foreign_keys = OFF;")
        for table in present:
            print(f"  DROP TABLE IF EXISTS {table}")
            conn.execute(f"DROP TABLE IF EXISTS {table};")
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON;")
        print(f"\nRollback complete. {len(present)} table(s) dropped.")
        print(f"To undo: cp \"{safety}\" \"{DB_PATH}\"")
    except Exception as e:
        conn.rollback()
        print(f"\nERROR during rollback: {e}")
        print(f"Database unchanged. Safety copy: {safety}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
