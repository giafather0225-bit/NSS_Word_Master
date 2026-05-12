"""
Migration 042 — Remove markdown bold from examples + fix wrong example sentences
==================================================================================
Two problems:

A) 112 example_1 values contain **bold** markdown (e.g., "The **archers** fired...").
   The frontend uses _esc() (HTML-only escape — no markdown renderer), so the
   asterisks appear literally on screen. Fix: strip all ** markers.

B) 4 examples are completely wrong — the sentence describes a different word:
   - heliocentric : example is about hemispheres
   - hemisphere   : example is about igloos
   - hemispheres  : example is about hypotheses
   - prey         : lion labeled as prey for cheetah (reversed — lion is predator)

Strategy: fix the 4 wrong sentences first (with correct content, no ** ),
then bulk-strip remaining ** from all other rows.

Idempotent: second run finds no ** remaining, updates 0 rows.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

WRONG_EXAMPLES = [
    (
        "heliocentric",
        "The heliocentric model places the sun at the center, with Earth and other planets orbiting around it.",
        "%hemispheres%",
    ),
    (
        "hemisphere",
        "The equator divides Earth into the Northern Hemisphere and the Southern Hemisphere.",
        "%igloo%",
    ),
    (
        "hemispheres",
        "The two hemispheres of the brain each control different functions of the body.",
        "%hypothesis%",
    ),
    (
        "prey",
        "The small fish was easy prey for the much larger shark that was hunting nearby.",
        "%lion%",
    ),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Step A: Fix the 4 completely wrong examples
    wrong_fixed = 0
    for word, new_ex, guard in WRONG_EXAMPLES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND example_1 LIKE ?",
            (word, guard),
        )
        if cur.fetchone()[0] > 0:
            cur.execute(
                "UPDATE us_academy_words SET example_1=? WHERE word=? AND example_1 LIKE ?",
                (new_ex, word, guard),
            )
            wrong_fixed += cur.rowcount

    # Step B: Strip remaining ** from all example_1 fields
    cur.execute(
        "SELECT COUNT(*) FROM us_academy_words WHERE example_1 LIKE '%**%'"
    )
    bold_count = cur.fetchone()[0]

    cur.execute(
        "UPDATE us_academy_words SET example_1 = REPLACE(example_1, '**', '') WHERE example_1 LIKE '%**%'"
    )
    bold_stripped = cur.rowcount

    conn.commit()
    conn.close()
    print(
        f"[042] Done — {wrong_fixed} wrong examples replaced, "
        f"{bold_stripped} rows had ** stripped (was {bold_count})."
    )


if __name__ == "__main__":
    run()
