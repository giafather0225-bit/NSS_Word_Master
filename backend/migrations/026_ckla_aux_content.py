"""
026_ckla_aux_content.py — Fill CKLA G3 Unit 1 spelling/grammar/morphology gaps
                           and add missing week 3 for units 6, 8, 11.

Idempotent: uses INSERT OR IGNORE for spelling rows, UPDATE only when value is '[]'.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


SPELLING_UNIT1 = [
    (1, 1, "short vowel review (CVC words)",
     json.dumps(["bat", "hen", "sit", "log", "bug", "cat", "red", "tip", "hot", "cut"]),
     json.dumps(["splash", "scratch"])),
    (1, 2, "long vowel silent-e (CVCe words)",
     json.dumps(["cape", "scene", "pine", "bone", "cube", "bake", "mole", "dune", "hike", "kite"]),
     json.dumps(["throne", "stripe"])),
    (1, 3, "digraphs and blends (sh, ch, th, wh; bl, cl, fl, sl)",
     json.dumps(["shape", "chest", "third", "wheat", "blade", "clam", "flame", "sled", "shack", "chose"]),
     json.dumps(["shrink", "splash"])),
]

SPELLING_WEEK3_MISSING = [
    (6, 3, "spelling patterns for /oo/ and /yoo/ sounds (oo, ue, ew, u_e, u)",
     json.dumps(["moon", "blue", "flew", "tune", "student", "proof", "clue", "brew", "rule", "flu"]),
     json.dumps(["bruise", "pursue"])),
    (8, 3, "review of /er/ spellings (er, ir, ur, ar, or, ear) in context",
     json.dumps(["fern", "bird", "burn", "dollar", "doctor", "heard", "stir", "curl", "pear", "word"]),
     json.dumps(["research", "murmur"])),
    (11, 3, "review of variant vowel and diphthong spellings",
     json.dumps(["caught", "crawl", "toil", "mouth", "fawn", "joy", "noun", "haul", "moist", "brow"]),
     json.dumps(["although", "devour"])),
]

GRAMMAR_UNIT1 = json.dumps(["complete sentences", "capitalization and end punctuation", "nouns and pronouns"])
MORPHOLOGY_UNIT1 = json.dumps(["compound words", "base words and root words"])


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # ── ckla_spelling: unit 1 (3 weeks) ──────────────────────────────────────
    for unit, week, pattern, words, challenge in SPELLING_UNIT1:
        cur.execute(
            "INSERT OR IGNORE INTO ckla_spelling (unit, week, pattern, words, challenge_words) VALUES (?,?,?,?,?)",
            (unit, week, pattern, words, challenge),
        )

    # ── ckla_spelling: week 3 for units 6, 8, 11 ─────────────────────────────
    for unit, week, pattern, words, challenge in SPELLING_WEEK3_MISSING:
        cur.execute(
            "INSERT OR IGNORE INTO ckla_spelling (unit, week, pattern, words, challenge_words) VALUES (?,?,?,?,?)",
            (unit, week, pattern, words, challenge),
        )

    # ── ckla_grammar: fill unit 1 empty array ────────────────────────────────
    cur.execute(
        "UPDATE ckla_grammar SET topics=? WHERE unit=1 AND (topics IS NULL OR TRIM(topics)='[]')",
        (GRAMMAR_UNIT1,),
    )

    # ── ckla_morphology: fill unit 1 empty array ─────────────────────────────
    cur.execute(
        "UPDATE ckla_morphology SET topics=? WHERE unit=1 AND (topics IS NULL OR TRIM(topics)='[]')",
        (MORPHOLOGY_UNIT1,),
    )

    conn.commit()
    print("[026] ckla_aux_content migration complete")
    print(f"  spelling unit 1: 3 weeks inserted (idempotent)")
    print(f"  spelling week 3 added for units 6, 8, 11 (idempotent)")
    print(f"  grammar  unit 1: {GRAMMAR_UNIT1}")
    print(f"  morphology unit 1: {MORPHOLOGY_UNIT1}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
