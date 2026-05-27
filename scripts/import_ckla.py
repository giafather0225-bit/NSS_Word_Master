"""
scripts/import_ckla.py — import CKLA G3 JSON → DB
Section: Academy
Dependencies: data/academy/ckla_g3/D1~D11.json, voca.db
API: none (CLI)

Usage:
    python3 scripts/import_ckla.py              # all 11 domains
    python3 scripts/import_ckla.py --dry-run    # print stats only, without touching the DB
    python3 scripts/import_ckla.py --domain 3   # a specific domain only
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB_PATH   = Path.home() / "NSS_Learning" / "database" / "voca.db"
DATA_DIR  = Path(__file__).resolve().parent.parent / "data" / "academy" / "ckla_g3"


# @tag ACADEMY @tag SYSTEM
def import_domain(conn: sqlite3.Connection, data: dict, dry_run: bool = False) -> dict:
    """Insert one domain's JSON into domains / lessons / questions / words / word_lesson.

    Returns stats dict.
    """
    stats = {
        "domain": data["domain_title"],
        "lessons": 0,
        "questions": 0,
        "words_new": 0,
        "words_seen": 0,
        "links": 0,
    }

    if dry_run:
        for l in data["lessons"]:
            stats["lessons"] += 1
            stats["questions"] += len(l.get("questions", []))
            stats["words_new"] += len(l.get("vocabulary", []))
        return stats

    # 1. domain upsert
    conn.execute("""
        INSERT INTO us_academy_domains (domain_num, title, source_pdf, lesson_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(domain_num) DO UPDATE SET
            title        = excluded.title,
            source_pdf   = excluded.source_pdf,
            lesson_count = excluded.lesson_count
    """, (
        _domain_num(data["source_pdf"]),
        data["domain_title"],
        data["source_pdf"],
        data["lesson_count"],
    ))
    domain_id = conn.execute(
        "SELECT id FROM us_academy_domains WHERE domain_num = ?",
        (_domain_num(data["source_pdf"]),)
    ).fetchone()[0]

    domain_num = _domain_num(data["source_pdf"])

    for lesson in data["lessons"]:
        # 2. lesson upsert
        conn.execute("""
            INSERT INTO us_academy_lessons
                (domain_id, domain_num, lesson_num, title,
                 passage, passage_chars, word_work_word)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain_num, lesson_num) DO UPDATE SET
                title          = excluded.title,
                passage        = excluded.passage,
                passage_chars  = excluded.passage_chars,
                word_work_word = excluded.word_work_word
        """, (
            domain_id,
            domain_num,
            lesson["lesson_num"],
            lesson["lesson_title"],
            lesson["passage"],
            len(lesson["passage"]),
            lesson.get("word_work_word") or None,
        ))
        lesson_id = conn.execute(
            "SELECT id FROM us_academy_lessons WHERE domain_num=? AND lesson_num=?",
            (domain_num, lesson["lesson_num"])
        ).fetchone()[0]
        stats["lessons"] += 1

        # 3. question upsert
        for q in lesson.get("questions", []):
            conn.execute("""
                INSERT INTO us_academy_questions
                    (lesson_id, question_num, kind, question_text, model_answer)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(lesson_id, question_num) DO UPDATE SET
                    kind          = excluded.kind,
                    question_text = excluded.question_text,
                    model_answer  = excluded.model_answer
            """, (
                lesson_id,
                q["num"],
                q["kind"],
                q["question"],
                q.get("model_answer") or "",
            ))
            stats["questions"] += 1

        # 4. word upsert + link
        for word in lesson.get("vocabulary", []):
            word = word.strip().lower()
            if not word:
                continue

            # Check whether the word already exists (duplicates allowed — same word can appear in other lessons)
            existing = conn.execute(
                "SELECT id FROM us_academy_words WHERE word = ? AND domain_num = ? AND lesson_num = ?",
                (word, domain_num, lesson["lesson_num"])
            ).fetchone()

            if existing:
                word_id = existing[0]
                stats["words_seen"] += 1
            else:
                conn.execute("""
                    INSERT INTO us_academy_words
                        (word, level, category, domain_num, lesson_num, is_active)
                    VALUES (?, 3, 'ckla', ?, ?, 1)
                """, (word, domain_num, lesson["lesson_num"]))
                word_id = conn.execute(
                    "SELECT id FROM us_academy_words WHERE word=? AND domain_num=? AND lesson_num=?",
                    (word, domain_num, lesson["lesson_num"])
                ).fetchone()[0]
                stats["words_new"] += 1

            # link table
            conn.execute("""
                INSERT OR IGNORE INTO us_academy_word_lesson (word_id, lesson_id)
                VALUES (?, ?)
            """, (word_id, lesson_id))
            stats["links"] += 1

    return stats


# @tag ACADEMY
def _domain_num(source_pdf: str) -> int:
    """'D3_Anth.pdf' → 3"""
    import re
    m = re.search(r"D(\d+)", source_pdf)
    return int(m.group(1)) if m else 0


# @tag ACADEMY
def main() -> None:
    dry_run   = "--dry-run" in sys.argv
    only_dom  = None
    if "--domain" in sys.argv:
        idx = sys.argv.index("--domain")
        only_dom = int(sys.argv[idx + 1])

    if dry_run:
        print("[dry-run] printing stats only, no DB changes.\n")

    conn = None
    if not dry_run:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

    total = {"lessons": 0, "questions": 0, "words_new": 0, "links": 0}

    domains = range(1, 12) if only_dom is None else [only_dom]
    for i in domains:
        path = DATA_DIR / f"D{i}.json"
        if not path.exists():
            print(f"  D{i}: JSON file not found — skipping")
            continue
        data = json.loads(path.read_text())
        stats = import_domain(conn, data, dry_run=dry_run)

        print(
            f"  D{i:>2}  {stats['domain'][:40]:<40}  "
            f"lessons{stats['lessons']:>3}  "
            f"questions{stats['questions']:>3}  "
            f"words(new){stats['words_new']:>3}  "
            f"links{stats['links']:>3}"
        )
        for k in ("lessons", "questions", "words_new", "links"):
            total[k] += stats[k]

    if not dry_run and conn:
        conn.commit()
        conn.close()

    print()
    print(f"  {'TOTAL':<44}  lessons{total['lessons']:>3}  questions{total['questions']:>3}  words(new){total['words_new']:>3}  links{total['links']:>3}")
    if not dry_run:
        print("\n  ✅ DB import complete")
    else:
        print("\n  (dry-run complete — nothing saved)")


if __name__ == "__main__":
    main()
