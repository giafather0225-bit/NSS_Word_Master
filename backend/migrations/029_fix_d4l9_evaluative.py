"""
029_fix_d4l9_evaluative.py — Add missing Evaluative question to D4 L9
                              (Julius Caesar: The Later Years, lesson_id=39).

Verifier flags this lesson for having 0 Evaluative questions (3 Lit + 5 Inf).
One Evaluative question is added to complete all 3 QA kinds.

Idempotent: INSERT skipped if an Evaluative question for lesson_id=39 already exists.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

QUESTION = {
    "lesson_id": 39,
    "kind": "Evaluative",
    "question_text": "Do you think Julius Caesar was more of a hero or a villain? Use evidence from the text to support your opinion.",
    "model_answer": (
        "Answers may vary. Hero: Caesar was a brilliant military leader who expanded Rome's "
        "territory, negotiated grain imports from Egypt, and strengthened the empire. "
        "Villain: He broke the law by crossing the Rubicon with his army and made himself "
        "dictator, concentrating power in a way that threatened the Roman Republic and "
        "ultimately led to his assassination."
    ),
}


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM us_academy_questions WHERE lesson_id=? AND kind='Evaluative'",
        (QUESTION["lesson_id"],),
    )
    if cur.fetchone()[0] > 0:
        print("[029] Evaluative question already exists for D4 L9 — skipped")
        return

    cur.execute(
        "SELECT COALESCE(MAX(question_num), 0) + 1 FROM us_academy_questions WHERE lesson_id=?",
        (QUESTION["lesson_id"],),
    )
    next_num = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO us_academy_questions (lesson_id, question_num, kind, question_text, model_answer) "
        "VALUES (:lesson_id, :question_num, :kind, :question_text, :model_answer)",
        {**QUESTION, "question_num": next_num},
    )
    conn.commit()
    print(f"[029] Evaluative question added to D4 L9 (id={cur.lastrowid})")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
