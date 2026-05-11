"""
031_fix_ocr_artifacts.py — Fix OCR split artifacts in CKLA G3 lesson titles,
                            question texts, and model answers.

Three categories:
  1. Lesson titles    — "J ulius Caesar" → "Julius Caesar"   (61 rows, D2–D11)
  2. Question texts:
       a. Strip classroom Pair-Share prefixes                 (71 questions)
       b. Fix leading OCR split "H ow" → "How"               (~213 rows, 2 exceptions)
       c. Fix hyphenation split "cold- blooded" → "cold-blooded"
  3. Model answers    — same leading-OCR + hyphen fixes       (~34 rows)

Idempotent: each UPDATE only fires when old_text != new_text.
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# ── Patterns ─────────────────────────────────────────────────────────────────
PAIR_SHARE_RE = re.compile(
    r'^(?:T hink|Think|W hat\??|What\??)\s+Pair\s+Share\s*:\s*',
    re.IGNORECASE,
)

LEADING_OCR_RE = re.compile(r'^([A-Z]) ([a-z])')

# Sentences that genuinely start with a single letter (NOT OCR artifacts)
LEADING_OCR_EXCEPTIONS = {127, 806}

HYPHEN_FIXES = [
    ("cold- blooded", "cold-blooded"),
    ("warm- blooded", "warm-blooded"),
    ("read- aloud",   "read-aloud"),
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def fix_title(title: str) -> str:
    # Fix letter OCR split: "J ulius" → "Julius"
    title = re.sub(r'^([A-Z]) ', r'\1', title)
    # Fix digit OCR split: "1 492" → "1492"
    title = re.sub(r'^(\d) (\d)', r'\1\2', title)
    return title


def strip_pair_share(text: str) -> str:
    return PAIR_SHARE_RE.sub('', text).strip()


def fix_leading_ocr(text: str) -> str:
    return LEADING_OCR_RE.sub(lambda m: m.group(1) + m.group(2), text)


def fix_hyphens(text: str) -> str:
    for bad, good in HYPHEN_FIXES:
        text = text.replace(bad, good)
    return text


def clean_question(qid: int, text: str) -> str:
    new = strip_pair_share(text)
    if qid not in LEADING_OCR_EXCEPTIONS:
        new = fix_leading_ocr(new)
    new = fix_hyphens(new)
    # Re-capitalise first letter if stripping left it lowercase
    if new and new[0].islower():
        new = new[0].upper() + new[1:]
    return new


def clean_answer(text: str) -> str:
    new = fix_leading_ocr(text)
    new = fix_hyphens(new)
    return new


# ── Main ─────────────────────────────────────────────────────────────────────
def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # 1. Lesson titles
    cur.execute("SELECT id, title FROM us_academy_lessons WHERE title GLOB '? *'")
    titles_fixed = 0
    for lid, title in cur.fetchall():
        new_title = fix_title(title)
        if new_title != title:
            cur.execute(
                "UPDATE us_academy_lessons SET title=? WHERE id=?",
                (new_title, lid),
            )
            titles_fixed += 1

    # 2. Question texts
    cur.execute("SELECT id, question_text FROM us_academy_questions WHERE question_text IS NOT NULL")
    pair_stripped = q_fixed = 0
    for qid, text in cur.fetchall():
        new_text = clean_question(qid, text)
        if new_text != text:
            had_pair_share = bool(PAIR_SHARE_RE.match(text))
            if had_pair_share:
                pair_stripped += 1
            cur.execute(
                "UPDATE us_academy_questions SET question_text=? WHERE id=?",
                (new_text, qid),
            )
            q_fixed += 1

    # 3. Model answers
    cur.execute(
        "SELECT id, model_answer FROM us_academy_questions "
        "WHERE model_answer IS NOT NULL AND model_answer != ''"
    )
    ma_fixed = 0
    for qid, text in cur.fetchall():
        new_text = clean_answer(text)
        if new_text != text:
            cur.execute(
                "UPDATE us_academy_questions SET model_answer=? WHERE id=?",
                (new_text, qid),
            )
            ma_fixed += 1

    conn.commit()
    print("[031] OCR artifact cleanup complete:")
    print(f"  lesson titles fixed   : {titles_fixed}")
    print(f"  Pair Share stripped   : {pair_stripped}")
    print(f"  question texts fixed  : {q_fixed}")
    print(f"  model answers fixed   : {ma_fixed}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
