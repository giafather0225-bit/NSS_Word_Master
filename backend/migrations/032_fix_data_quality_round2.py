"""
032_fix_data_quality_round2.py — Second-pass data quality fixes found during D2–D11 smoke test.

Four categories:
  1. Lesson title typo   — D3 L9 "AClean Bill of Health" → "A Clean Bill of Health" (missing space)
  2. Duplicate lesson    — D4 L11 (id=41) is identical to D4 L12 (id=42); deactivate
  3. Orphan questions    — D4 L11's 9 questions: 6 duplicates deleted, 3 unique ones reassigned to L12
                          Delete: id=307,308,310 (Eval dup), 306,311 (Inf dup), 309 (Lit dup)
                          Reassign to L12: id=880 (Inf), 878,879 (Lit)
  4. Hyphen artifacts    — 7 question/model_answer rows with "word- word" → "word-word"
                          (pattern-breakers, decision-making, self-government ×2,
                           fastest-growing, post-graduate, non-living)

Idempotent: each UPDATE/DELETE only fires when the old value still matches.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

HYPHEN_FIXES_Q = [
    # (id, old_fragment, new_fragment)
    (738, "fastest- growing", "fastest-growing"),
]

HYPHEN_FIXES_A = [
    (134, "pattern- breakers",  "pattern-breakers"),
    (194, "decision- making",   "decision-making"),
    (710, "self- government",   "self-government"),
    (711, "self- government",   "self-government"),
    (746, "post- graduate",     "post-graduate"),
    (776, "non- living",        "non-living"),
]


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    fixed = 0

    # 1. D3 L9 title typo
    cur.execute(
        "UPDATE us_academy_lessons SET title='A Clean Bill of Health' "
        "WHERE id=30 AND title='AClean Bill of Health'",
    )
    if cur.rowcount:
        print("[032] D3 L9 title fixed: 'AClean Bill of Health' → 'A Clean Bill of Health'")
        fixed += 1
    else:
        print("[032] D3 L9 title: already correct or not found — skipped")

    # 2. Deactivate duplicate D4 L11 (id=41 identical to id=42)
    cur.execute(
        "UPDATE us_academy_lessons SET is_active=0 "
        "WHERE id=41 AND is_active=1",
    )
    if cur.rowcount:
        print("[032] D4 L11 (id=41) deactivated — duplicate of L12 (id=42)")
        fixed += 1
    else:
        print("[032] D4 L11 (id=41): already inactive — skipped")

    # 3. Handle orphan questions from deactivated D4 L11
    #    a. Delete 6 duplicate questions (same text exists under L12)
    dup_ids = [307, 308, 310, 306, 311, 309]
    placeholders = ",".join("?" * len(dup_ids))
    cur.execute(f"DELETE FROM us_academy_questions WHERE id IN ({placeholders})", dup_ids)
    deleted = cur.rowcount
    print(f"[032] D4 L11 duplicate questions deleted: {deleted} rows")
    fixed += deleted

    #    b. Reassign 3 unique L11 questions to L12 (id=42) with new question_num
    #       (L12 already occupies num 1-9; assign 10, 11, 12)
    reassign = [(880, 10), (878, 11), (879, 12)]
    reassigned = 0
    for qid, new_num in reassign:
        cur.execute(
            "UPDATE us_academy_questions SET lesson_id=42, question_num=? WHERE id=? AND lesson_id=41",
            (new_num, qid),
        )
        if cur.rowcount:
            reassigned += 1
    print(f"[032] D4 L11 unique questions reassigned to L12: {reassigned} rows")
    fixed += reassigned

    # 3a. Hyphen artifacts in question_text
    for qid, old, new in HYPHEN_FIXES_Q:
        cur.execute("SELECT question_text FROM us_academy_questions WHERE id=?", (qid,))
        row = cur.fetchone()
        if row and old in row[0]:
            cur.execute(
                "UPDATE us_academy_questions SET question_text=REPLACE(question_text,?,?) WHERE id=?",
                (old, new, qid),
            )
            print(f"[032] q id={qid} question_text: '{old}' → '{new}'")
            fixed += 1
        else:
            print(f"[032] q id={qid} question_text: already fixed or not found — skipped")

    # 3b. Hyphen artifacts in model_answer
    for qid, old, new in HYPHEN_FIXES_A:
        cur.execute("SELECT model_answer FROM us_academy_questions WHERE id=?", (qid,))
        row = cur.fetchone()
        if row and row[0] and old in row[0]:
            cur.execute(
                "UPDATE us_academy_questions SET model_answer=REPLACE(model_answer,?,?) WHERE id=?",
                (old, new, qid),
            )
            print(f"[032] q id={qid} model_answer: '{old}' → '{new}'")
            fixed += 1
        else:
            print(f"[032] q id={qid} model_answer: already fixed or not found — skipped")

    conn.commit()
    print(f"\n[032] Done: {fixed} items fixed")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
