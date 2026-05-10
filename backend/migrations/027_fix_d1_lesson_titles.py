"""
027_fix_d1_lesson_titles.py — Fix OCR-artifact lesson titles in Domain 1 (Classic Tales)
                               and deactivate ghost lesson not present in source JSON.

OCR artifacts: "T he" → "The", "M r." → "Mr.", "D ulce" → "Dulce", "T oad's" → "Toad's"
Ghost lesson:  id=11, lesson_num=11 ("The Return of Toad, Part I") — not in D1.json
               (JSON goes 10 → 12 → 13; lesson_num 11 was inserted from a prior import)

Idempotent: uses WHERE title=<broken_title> so re-running is safe.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

TITLE_FIXES = [
    (1,  "T he River Bank, Part I",                   "The River Bank, Part I"),
    (2,  "T he River Bank, Part II",                  "The River Bank, Part II"),
    (3,  "T he Open Road",                             "The Open Road"),
    (4,  "T he Wild Wood",                             "The Wild Wood"),
    (5,  "M r. Badger",                                "Mr. Badger"),
    (6,  "D ulce Domum, Part I",                       "Dulce Domum, Part I"),
    (7,  "D ulce Domum, Part II",                      "Dulce Domum, Part II"),
    (8,  "M r. Toad",                                  "Mr. Toad"),
    (9,  "T oad's Adventures",                         "Toad's Adventures"),
    (10, "T he Further Adventures of Toad, Part I",   "The Further Adventures of Toad, Part I"),
    (12, "T he Return of Toad, Part I",                "The Return of Toad, Part I"),
    (116,"T he Return of Toad, Part II",               "The Return of Toad, Part II"),
]


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    fixed = 0
    for lesson_id, old_title, new_title in TITLE_FIXES:
        cur.execute(
            "UPDATE us_academy_lessons SET title=? WHERE id=? AND title=?",
            (new_title, lesson_id, old_title),
        )
        if cur.rowcount:
            fixed += 1
            print(f"  [{lesson_id:3d}] '{old_title}' → '{new_title}'")

    # Deactivate ghost lesson (lesson_num=11, not present in D1.json)
    cur.execute(
        "UPDATE us_academy_lessons SET is_active=0 WHERE id=11 AND domain_num=1 AND lesson_num=11",
    )
    ghost = cur.rowcount
    if ghost:
        print("  [ghost] id=11 lesson_num=11 deactivated")

    # Delete orphan questions from deactivated ghost lesson (id=11, lesson_num=11)
    # lesson_id=12 already has its own questions; these 6 are duplicates from a prior import.
    cur.execute(
        "DELETE FROM us_academy_questions WHERE lesson_id=11",
    )
    deleted_q = cur.rowcount

    conn.commit()
    print(f"\n[027] D1 title fix complete: {fixed} titles updated, "
          f"{ghost} ghost lesson deactivated, {deleted_q} orphan questions deleted")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
