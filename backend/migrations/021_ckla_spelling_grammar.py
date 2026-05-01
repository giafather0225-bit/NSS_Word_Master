"""
migrations/021_ckla_spelling_grammar.py — CKLA spelling words + grammar/morphology tables
Section: CKLA
Idempotent — safe to run repeatedly.

Creates:
  ckla_spelling    — weekly spelling word lists per unit (JSON arrays stored as TEXT)
  ckla_grammar     — grammar topics per unit (JSON array stored as TEXT)
  ckla_morphology  — morphology topics per unit (JSON array stored as TEXT)

Seeds data from data/ckla_source/spelling_words.json and grammar_morphology.json
if those files exist.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "ckla_source"

_CREATE_SPELLING = """
CREATE TABLE IF NOT EXISTS ckla_spelling (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    unit           INTEGER NOT NULL,
    week           INTEGER NOT NULL,
    pattern        TEXT    NOT NULL DEFAULT '',
    words          TEXT    NOT NULL DEFAULT '[]',
    challenge_words TEXT   NOT NULL DEFAULT '[]',
    UNIQUE (unit, week)
)
"""

_CREATE_GRAMMAR = """
CREATE TABLE IF NOT EXISTS ckla_grammar (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    unit    INTEGER NOT NULL UNIQUE,
    topics  TEXT    NOT NULL DEFAULT '[]'
)
"""

_CREATE_MORPHOLOGY = """
CREATE TABLE IF NOT EXISTS ckla_morphology (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    unit    INTEGER NOT NULL UNIQUE,
    topics  TEXT    NOT NULL DEFAULT '[]'
)
"""


def _seed_spelling(conn: sqlite3.Connection) -> int:
    path = DATA_DIR / "spelling_words.json"
    if not path.exists():
        print("[migration 021] spelling_words.json not found — skipping spelling seed")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    seeded = 0
    for unit_data in data:
        unit = unit_data.get("unit")
        if not unit:
            continue
        for week_num in range(1, 5):
            key = f"week{week_num}"
            week_data = unit_data.get(key)
            if not week_data:
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO ckla_spelling (unit, week, pattern, words, challenge_words) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    unit,
                    week_num,
                    week_data.get("pattern", ""),
                    json.dumps(week_data.get("words", [])),
                    json.dumps(week_data.get("challenge_words", [])),
                ),
            )
            seeded += cur.rowcount
    return seeded


def _seed_grammar_morphology(conn: sqlite3.Connection) -> tuple[int, int]:
    path = DATA_DIR / "grammar_morphology.json"
    if not path.exists():
        print("[migration 021] grammar_morphology.json not found — skipping seed")
        return 0, 0
    data = json.loads(path.read_text(encoding="utf-8"))
    g_seeded = 0
    m_seeded = 0
    for unit_data in data:
        unit = unit_data.get("unit")
        if not unit:
            continue
        cur = conn.execute(
            "INSERT OR IGNORE INTO ckla_grammar (unit, topics) VALUES (?, ?)",
            (unit, json.dumps(unit_data.get("grammar", []))),
        )
        g_seeded += cur.rowcount
        cur = conn.execute(
            "INSERT OR IGNORE INTO ckla_morphology (unit, topics) VALUES (?, ?)",
            (unit, json.dumps(unit_data.get("morphology", []))),
        )
        m_seeded += cur.rowcount
    return g_seeded, m_seeded


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"[migration 021] DB not found at {DB_PATH}; skipping.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}

        created: list[str] = []
        for tbl, ddl in [
            ("ckla_spelling",   _CREATE_SPELLING),
            ("ckla_grammar",    _CREATE_GRAMMAR),
            ("ckla_morphology", _CREATE_MORPHOLOGY),
        ]:
            if tbl not in tables:
                conn.execute(ddl)
                created.append(tbl)

        if created:
            conn.commit()
            for t in created:
                print(f"[migration 021] Created table {t}")
        else:
            print("[migration 021] Tables already present — checking seed data.")

        spell_seeded = _seed_spelling(conn)
        g_seeded, m_seeded = _seed_grammar_morphology(conn)
        conn.commit()

        if spell_seeded:
            print(f"[migration 021] Seeded {spell_seeded} spelling week(s).")
        if g_seeded:
            print(f"[migration 021] Seeded {g_seeded} grammar unit(s).")
        if m_seeded:
            print(f"[migration 021] Seeded {m_seeded} morphology unit(s).")
        if not any([spell_seeded, g_seeded, m_seeded]):
            print("[migration 021] All seed data already present.")

    finally:
        conn.close()

    print("[migration 021] complete.")


if __name__ == "__main__":
    migrate()
