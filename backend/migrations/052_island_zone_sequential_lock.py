"""
Migration 052 — island_zone_status: enforce sequential zone unlock

Problem (2026-05-13): migration 018 seeded forest/ocean/savanna/space/legend
all as is_unlocked=1. ISLAND_SPEC §Zone requires sequential unlock:
  forest (default start) → first char complete → ocean → ... → legend.

Fix: lock any zone whose unlock condition is not yet satisfied, based on
actual is_completed data in island_character_progress.

Lock chain: forest → ocean → savanna → space → legend
  - forest: always unlocked (onboarding default)
  - ocean  : unlock if forest has ≥1 is_completed character
  - savanna: unlock if ocean  has ≥1 is_completed character
  - space  : unlock if savanna has ≥1 is_completed character
  - legend : unlock if all 4 main zones each have ≥1 is_completed character

Idempotent: safe to re-run.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_CHAIN = ["forest", "ocean", "savanna", "space"]


def run(con: sqlite3.Connection) -> None:
    cur = con.cursor()

    # Check table exists (guard for fresh installs without island tables).
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='island_zone_status'"
    )
    if not cur.fetchone():
        print("  [052] island_zone_status not found — skip")
        return

    # Fetch completed-character count per zone.
    cur.execute("""
        SELECT c.zone, COUNT(cp.id)
        FROM island_characters c
        LEFT JOIN island_character_progress cp
            ON cp.character_id = c.id AND cp.is_completed = 1
        GROUP BY c.zone
    """)
    completed_by_zone: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}

    # Derive correct is_unlocked for each zone in chain order.
    correct: dict[str, int] = {}
    for i, zone in enumerate(_CHAIN):
        if i == 0:
            # Forest is always unlocked (starting zone).
            correct[zone] = 1
        else:
            prev_zone = _CHAIN[i - 1]
            correct[zone] = 1 if completed_by_zone.get(prev_zone, 0) >= 1 else 0

    # Legend: all 4 main zones need ≥1 completed character.
    all_complete = all(completed_by_zone.get(z, 0) >= 1 for z in _CHAIN)
    correct["legend"] = 1 if all_complete else 0

    # Apply corrections.
    cur.execute("SELECT zone, is_unlocked FROM island_zone_status")
    current: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}

    changed = 0
    for zone, should_be_unlocked in correct.items():
        was = current.get(zone, -1)
        if was != should_be_unlocked:
            if should_be_unlocked:
                cur.execute(
                    "UPDATE island_zone_status SET is_unlocked=1 WHERE zone=?", (zone,)
                )
            else:
                cur.execute(
                    "UPDATE island_zone_status SET is_unlocked=0, unlocked_at=NULL WHERE zone=?",
                    (zone,),
                )
            print(f"  [052] {zone}: is_unlocked {was} → {should_be_unlocked}")
            changed += 1

    if changed == 0:
        print("  [052] island_zone_status already correct — no changes")

    con.commit()


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as con:
        run(con)
    print("Migration 052 complete.")
