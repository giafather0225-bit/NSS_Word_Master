"""
Migration 039 — Fix circular definitions and miscellaneous data errors
=======================================================================
Issues fixed:

A) Circular definitions (definition uses the word itself):
   - indigo      : removes "(indigo plants)" parenthetical
   - quakers     : "commonly called Quakers" → Grade-3 description
   - solstice    : contains "summer solstice" / "winter solstice" in-definition
   - wetland     : "Wetland is usually used in the plural form wetlands."
   - wetlands    : same issue + trailing self-reference

B) Miscellaneous data error:
   - false starts: tagged adjective with definition for 'false' (wrong word entirely)
                   → noun with correct definition

Idempotent: every UPDATE guarded by definition or POS fragment match.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (word, new_pos, new_definition, guard_fragment)
FIXES = [
    ("indigo", "noun",
     "a deep blue-purple color; also a plant that produces a dark blue dye",
     "indigo plants"),

    ("quakers", "noun",
     "members of a Christian group called the Religious Society of Friends, known for simple living and peaceful beliefs",
     "commonly called Quakers"),

    ("solstice", "noun",
     "one of two days each year when the sun is at its farthest point north or south, giving the longest or shortest day of the year",
     "summer solstice"),

    ("wetland", "noun",
     "an area of land that is always wet or flooded, such as a marsh or swamp, and is home to many plants and animals",
     "Wetland is usually used"),

    ("wetlands", "noun",
     "areas of land that are always wet or flooded, such as marshes and swamps, and are home to many plants and animals",
     "Wetland is usually used"),

    ("false starts", "noun",
     "failed attempts to begin something; situations where you start doing something but have to stop and begin again",
     "not true, genuine, or honest"),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    updated = 0
    skipped = 0

    for word, new_pos, new_def, guard in FIXES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND (definition LIKE ? OR part_of_speech LIKE ?)",
            (word, f"%{guard}%", f"%{guard}%"),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue
        cur.execute(
            """UPDATE us_academy_words
               SET part_of_speech=?, definition=?
             WHERE word=? AND (definition LIKE ? OR part_of_speech LIKE ?)""",
            (new_pos, new_def, word, f"%{guard}%", f"%{guard}%"),
        )
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"[039] Done — {updated} rows updated, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
