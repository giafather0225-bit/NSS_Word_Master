"""
Migration 041 — Replace 'of, relating to' dictionary-style definitions
=======================================================================
Ten adjectives have formal MW-style definitions beginning with
'of, relating to' or 'relating to' that are inappropriate for Grade 3.
Rewrites each with a child-friendly explanation. Example sentences
preserved where good; replaced where they illustrate the wrong sense.

Idempotent: guarded by WHERE definition LIKE '%relating to%'.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (word, new_definition, new_example, guard_fragment)
FIXES = [
    (
        "agricultural",
        "having to do with farming and the growing of crops or raising of animals",
        "The agricultural region was covered with wheat fields and cattle ranches.",
        "relating to or used in farming",
    ),
    (
        "alpine",
        "found in or having to do with high mountain areas, especially the Alps",
        "The alpine meadow was filled with wildflowers and cool, thin air.",
        "Relating to or characteristic of alps",
    ),
    (
        "ancestral",
        "belonging to or coming from one's ancestors; passed down through family generations",
        "They traveled to their ancestral homeland to learn about their family's history.",
        "of, relating to, or coming from an ancestor",
    ),
    (
        "astronomical",
        "having to do with astronomy and the study of stars, planets, and outer space; also used to describe something extremely large",
        "The astronomical observatory had a giant telescope for studying distant galaxies.",
        "of or relating to astronomy",
    ),
    (
        "domestic",
        "having to do with the home, family life, or a country's own affairs rather than foreign ones",
        "She enjoyed domestic activities like cooking and decorating the house.",
        "relating to a household or a family",
    ),
    (
        "marine",
        "living in, found in, or having to do with the sea or ocean",
        "Marine biologists study the amazing creatures that live in the ocean.",
        "of or relating to the sea",
    ),
    (
        "polar",
        "found in or having to do with the areas near the North or South Pole, where it is extremely cold",
        "Polar bears are built for survival in the freezing Arctic temperatures.",
        "of or relating to the north pole or south pole",
    ),
    (
        "prehistoric",
        "belonging to the time period before people kept written records of history",
        "Dinosaurs were prehistoric animals that lived millions of years before humans.",
        "relating to or existing in the time before written history began",
    ),
    (
        "respiratory",
        "having to do with breathing and the body parts used for breathing, such as the lungs, nose, and windpipe",
        "A cold can cause respiratory problems like a runny nose and difficulty breathing.",
        "of, relating to, or concerned with breathing",
    ),
    (
        "terrestrial",
        "living on land rather than in water or in the air; having to do with the planet Earth",
        "Dogs, horses, and elephants are terrestrial animals that live on land.",
        "relating to the earth or its people",
    ),
]


def run(db_path: str = str(DB_PATH)) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    updated = 0
    skipped = 0

    for word, new_def, new_ex, guard in FIXES:
        cur.execute(
            "SELECT COUNT(*) FROM us_academy_words WHERE word=? AND definition LIKE ?",
            (word, f"%{guard}%"),
        )
        if cur.fetchone()[0] == 0:
            skipped += 1
            continue
        cur.execute(
            """UPDATE us_academy_words
               SET definition=?, example_1=?
             WHERE word=? AND definition LIKE ?""",
            (new_def, new_ex, word, f"%{guard}%"),
        )
        updated += cur.rowcount

    conn.commit()
    conn.close()
    print(f"[041] Done — {updated} rows updated, {skipped} already fixed / not found.")


if __name__ == "__main__":
    run()
