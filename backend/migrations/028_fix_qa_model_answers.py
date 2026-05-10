"""
028_fix_qa_model_answers.py — QA quality fixes for CKLA G3
  1. Delete 12 "Pair Share" classroom-activity prompts not suitable for solo app
  2. Add model_answer to 2 real inferential/evaluative questions missing it
  3. Delete excess same-kind questions from 7 lessons where one kind > 6

Idempotent: DELETE WHERE id IN (...) is safe to re-run; UPDATE WHERE model_answer IS NULL
            protects already-set values.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Classroom Pair Share / activity prompts — not answerable solo
PAIR_SHARE_IDS = [121, 162, 236, 262, 279, 297, 404, 450, 471, 578, 638, 662]

# Excess same-kind questions per lesson (keep only 6 per kind)
EXCESS_KIND_IDS = [
    856,        # D3 L4 — 7th Inferential
    224,        # D3 L9 — 7th Inferential
    271, 272,   # D4 L6 — 7th & 8th Evaluative
    903,        # D7 L3 — 7th Inferential
    702, 703,   # D10 L5 — 7th & 8th Inferential
    752, 753,   # D10 L10 — 7th & 8th Inferential
    818, 819,   # D11 L7 — 7th & 8th Evaluative
]

MODEL_ANSWERS = [
    (
        1048,
        "Inferential",
        "They need to use the underground passage because the weasels and stoats have taken over Toad Hall, blocking all the main entrances and guarding them heavily.",
    ),
    (
        198,
        "Evaluative",
        "The skull protects the brain, which controls thinking and movement, while the ribs protect the heart and lungs, which control blood circulation and breathing. Both form hard bony cages around soft vital organs, but the skull is a solid dome while the ribs form a flexible cage that expands when we breathe.",
    ),
]


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # 1. Delete Pair Share questions
    placeholders = ",".join("?" * len(PAIR_SHARE_IDS))
    cur.execute(f"DELETE FROM us_academy_questions WHERE id IN ({placeholders})", PAIR_SHARE_IDS)
    deleted_ps = cur.rowcount
    print(f"  Pair Share deleted: {deleted_ps} rows (expected {len(PAIR_SHARE_IDS)})")

    # 2. Delete excess same-kind questions
    placeholders = ",".join("?" * len(EXCESS_KIND_IDS))
    cur.execute(f"DELETE FROM us_academy_questions WHERE id IN ({placeholders})", EXCESS_KIND_IDS)
    deleted_ex = cur.rowcount
    print(f"  Excess-kind deleted: {deleted_ex} rows (expected {len(EXCESS_KIND_IDS)})")

    # 3. Add model_answer where missing
    updated = 0
    for qid, kind, answer in MODEL_ANSWERS:
        cur.execute(
            "UPDATE us_academy_questions SET model_answer=? WHERE id=? AND (model_answer IS NULL OR model_answer='')",
            (answer, qid),
        )
        if cur.rowcount:
            updated += 1
            print(f"  [id={qid}] model_answer set ({kind})")
        else:
            print(f"  [id={qid}] skipped (already set or not found)")

    conn.commit()
    print(
        f"\n[028] QA fix complete: "
        f"{deleted_ps} pair-share deleted, "
        f"{deleted_ex} excess-kind deleted, "
        f"{updated} model_answers added"
    )


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
