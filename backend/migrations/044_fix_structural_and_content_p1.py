"""
Migration 044 — Fix structural bugs + content errors (P1)
==========================================================
Issues fixed:

A) us_academy_word_lesson — 18 duplicate mappings (D1/D4 L11-L13 crossover)
   D1L12 words appear in both lesson_id=11 AND lesson_id=12 (correct is 12).
   D1L13 words appear in both lesson_id=12 AND lesson_id=116 (correct is 116).
   D4L12 words appear in both lesson_id=41 AND lesson_id=42 (correct is 42).
   D4L13 words appear in both lesson_id=42 AND lesson_id=146 (correct is 146).
   Fix: delete the wrong-lesson-id rows from us_academy_word_lesson.

B) us_academy_lessons — duplicate titles for D1L11/L12 and D4L11/L12
   D1L11 (lesson_id=11) has the same title as D1L12: "The Return of Toad, Part I"
     → Correct title: "The Further Adventures of Toad, Part II"
   D4L11 (lesson_id=41) same title as D4L12: "The Western and Eastern Empires"
     → Correct title: "The Western and Eastern Empires, Part I"
   D4L12 (lesson_id=42) duplicate of D4L11
     → Correct title: "The Western and Eastern Empires, Part II"

C) us_academy_domains — lesson_count off by 1 for D1 and D4
   Both declared lesson_count=12 but actually have 13 lessons.

D) us_academy_words — content errors
   - buffer     : definition is "a pale orange yellow" (the color buff, not buffer)
                  → proper Grade-3 definition for buffer zone / protective barrier
   - disruptions: POS=verb, def="to cause disorder in" (it's a noun)
   - shamans    : MW colon pattern in definition
   - uncivilized: "having, relating to, or being like" style

Idempotent: every UPDATE guarded by current (wrong) value.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# word_ids to remove from the wrong lesson_id (determined by analysis)
# D1: words that belong to L12 but are also in lesson_id=11 (the phantom duplicate)
D1_L12_WORD_IDS = [55, 56, 57, 58, 59]   # imprisoned, sentries, startled, surveyed, warily
# D1: words that belong to L13 but are also in lesson_id=12
D1_L13_WORD_IDS = [60, 61, 62, 63, 64]   # deafening, expedition, immense, modest, sentinels
# D4: words that belong to L12 but are also in lesson_id=41
D4_L12_WORD_IDS = [251, 252, 253, 254]   # complex, dominant, persecuted, vision
# D4: words that belong to L13 but are also in lesson_id=42
D4_L13_WORD_IDS = [255, 256, 257, 258]   # engineering, feats, legacy, thrive


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ── A. Remove duplicate word_lesson rows ─────────────────────────────────
    wl_removed = 0

    # D1L12 words wrongly in lesson_id=11
    for wid in D1_L12_WORD_IDS:
        cur.execute(
            "DELETE FROM us_academy_word_lesson WHERE lesson_id=11 AND word_id=?",
            (wid,),
        )
        wl_removed += cur.rowcount

    # D1L13 words wrongly in lesson_id=12
    for wid in D1_L13_WORD_IDS:
        cur.execute(
            "DELETE FROM us_academy_word_lesson WHERE lesson_id=12 AND word_id=?",
            (wid,),
        )
        wl_removed += cur.rowcount

    # D4L12 words wrongly in lesson_id=41
    for wid in D4_L12_WORD_IDS:
        cur.execute(
            "DELETE FROM us_academy_word_lesson WHERE lesson_id=41 AND word_id=?",
            (wid,),
        )
        wl_removed += cur.rowcount

    # D4L13 words wrongly in lesson_id=42
    for wid in D4_L13_WORD_IDS:
        cur.execute(
            "DELETE FROM us_academy_word_lesson WHERE lesson_id=42 AND word_id=?",
            (wid,),
        )
        wl_removed += cur.rowcount

    # ── B. Fix duplicate lesson titles ───────────────────────────────────────
    lesson_fixed = 0

    cur.execute(
        "UPDATE us_academy_lessons SET title=? WHERE id=11 AND title=?",
        ("The Further Adventures of Toad, Part II", "The Return of Toad, Part I"),
    )
    lesson_fixed += cur.rowcount

    cur.execute(
        "UPDATE us_academy_lessons SET title=? WHERE id=41 AND title=?",
        ("The Western and Eastern Empires, Part I", "The Western and Eastern Empires"),
    )
    lesson_fixed += cur.rowcount

    cur.execute(
        "UPDATE us_academy_lessons SET title=? WHERE id=42 AND title=?",
        ("The Western and Eastern Empires, Part II", "The Western and Eastern Empires"),
    )
    lesson_fixed += cur.rowcount

    # ── C. Fix domain lesson_count ───────────────────────────────────────────
    domain_fixed = 0

    cur.execute(
        "UPDATE us_academy_domains SET lesson_count=13 WHERE domain_num=1 AND lesson_count=12",
    )
    domain_fixed += cur.rowcount

    cur.execute(
        "UPDATE us_academy_domains SET lesson_count=13 WHERE domain_num=4 AND lesson_count=12",
    )
    domain_fixed += cur.rowcount

    # ── D. Fix word definitions ───────────────────────────────────────────────
    word_fixed = 0

    # buffer: wrong definition entirely
    cur.execute(
        """UPDATE us_academy_words
           SET definition=?, example_1=?
           WHERE word='buffer' AND definition LIKE '%pale orange%'""",
        (
            "a zone, area, or thing that separates two groups or forces and protects each from the other",
            "The small colony served as a buffer between the English settlements and the French-controlled territory.",
        ),
    )
    word_fixed += cur.rowcount

    # disruptions: verb → noun + proper definition + proper example
    cur.execute(
        """UPDATE us_academy_words
           SET part_of_speech='noun', definition=?, example_1=?
           WHERE word='disruptions' AND part_of_speech='verb'""",
        (
            "events or situations that interrupt or disturb the normal flow of something",
            "The disruptions caused by the storm kept students home from school for two days.",
        ),
    )
    word_fixed += cur.rowcount

    # shamans: MW colon pattern
    cur.execute(
        """UPDATE us_academy_words
           SET definition=?
           WHERE word='shamans' AND definition LIKE '%shamanism:%'""",
        (
            "spiritual leaders in some cultures who are believed to have the ability to communicate "
            "with the spirit world and use special powers to heal people or predict the future",
        ),
    )
    word_fixed += cur.rowcount

    # uncivilized: "having, relating to, or being like"
    cur.execute(
        """UPDATE us_academy_words
           SET definition=?
           WHERE word='uncivilized' AND definition LIKE '%relating to%'""",
        (
            "describing a society or behavior that lacks education, order, or basic social customs; "
            "considered rough, wild, or not yet developed",
        ),
    )
    word_fixed += cur.rowcount

    conn.commit()
    conn.close()
    print(
        f"[044] Done — "
        f"{wl_removed} duplicate word_lesson rows removed, "
        f"{lesson_fixed} lesson titles fixed, "
        f"{domain_fixed} domain lesson_counts updated, "
        f"{word_fixed} word definitions corrected."
    )


if __name__ == "__main__":
    run()
