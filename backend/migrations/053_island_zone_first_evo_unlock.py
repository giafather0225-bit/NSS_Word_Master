"""
Migration 053 — island_zone_status: correct unlock chain to use first-evolution criterion

Problem (2026-05-13): migration 052 used is_completed=1 (final evolution) to determine
zone unlock eligibility. The correct rule per ISLAND_SPEC is:

  "Zone N unlocks when Zone N-1 has ≥1 character whose stage is NOT 'baby'"
  (i.e., first evolution complete: stage in mid_a, mid_b, final_a, final_b)

  Legend unlocks when ALL four main zones each have ≥1 first-evolution character.

Current DB state after 052: space=0, legend=0 — both should be unlocked because:
  - savanna has Mane at mid_a  → space should be unlocked
  - all 4 zones have first-evo  → legend should be unlocked

Idempotent: safe to re-run.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

_CHAIN = ["forest", "ocean", "savanna", "space"]
_FIRST_EVO_STAGES = ("mid_a", "mid_b", "final_a", "final_b")


def run(con: sqlite3.Connection) -> None:
    cur = con.cursor()

    # Guard: table must exist.
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='island_zone_status'"
    )
    if not cur.fetchone():
        print("  [053] island_zone_status not found — skip")
        return

    # Count characters with first-evolution done (stage != 'baby') per zone.
    placeholders = ",".join("?" * len(_FIRST_EVO_STAGES))
    cur.execute(f"""
        SELECT c.zone, COUNT(cp.id)
        FROM island_characters c
        LEFT JOIN island_character_progress cp
            ON cp.character_id = c.id
            AND cp.stage IN ({placeholders})
        GROUP BY c.zone
    """, _FIRST_EVO_STAGES)
    first_evo_by_zone: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}

    # Compute correct is_unlocked for each zone.
    correct: dict[str, int] = {}
    for i, zone in enumerate(_CHAIN):
        if i == 0:
            correct[zone] = 1  # forest always unlocked
        else:
            prev_zone = _CHAIN[i - 1]
            correct[zone] = 1 if first_evo_by_zone.get(prev_zone, 0) >= 1 else 0

    # Legend: all 4 main zones need ≥1 first-evolution character.
    all_first_evo = all(first_evo_by_zone.get(z, 0) >= 1 for z in _CHAIN)
    correct["legend"] = 1 if all_first_evo else 0

    # Apply corrections.
    cur.execute("SELECT zone, is_unlocked FROM island_zone_status")
    current: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}

    changed = 0
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    for zone, should_be_unlocked in correct.items():
        was = current.get(zone, -1)
        if was != should_be_unlocked:
            if should_be_unlocked:
                cur.execute(
                    "UPDATE island_zone_status SET is_unlocked=1, unlocked_at=? WHERE zone=?",
                    (now, zone),
                )
            else:
                cur.execute(
                    "UPDATE island_zone_status SET is_unlocked=0, unlocked_at=NULL WHERE zone=?",
                    (zone,),
                )
            print(f"  [053] {zone}: is_unlocked {was} → {should_be_unlocked}")
            changed += 1

    if changed == 0:
        print("  [053] island_zone_status already correct — no changes")

    con.commit()


if __name__ == "__main__":
    with sqlite3.connect(DB_PATH) as con:
        run(con)
    print("Migration 053 complete.")
