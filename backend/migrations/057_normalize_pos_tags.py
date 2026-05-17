"""
migrations/057_normalize_pos_tags.py — Standardize POS tags to canonical forms.

study_items.extra_data stores POS as JSON {"pos": "..."} with 18+ variants
(v, n, adj, adv, n., v., adj., adv., (n), (v), (adj), (adv), (conj), prep,
conj, pron …).  words.pos has the same loose format.

Normalizes all values to one of:
  noun | verb | adjective | adverb | conjunction | preposition | pronoun

Idempotent: safe to re-run (already-canonical rows are left untouched).
"""

import json
from typing import Dict, Optional
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# Map every known variant → canonical form
POS_MAP: Dict[str, str] = {
    # noun variants
    "n":      "noun",
    "n.":     "noun",
    "(n)":    "noun",
    # verb variants
    "v":      "verb",
    "v.":     "verb",
    "(v)":    "verb",
    # adjective variants
    "adj":    "adjective",
    "adj.":   "adjective",
    "(adj)":  "adjective",
    # adverb variants
    "adv":    "adverb",
    "adv.":   "adverb",
    "(adv)":  "adverb",
    # conjunction variants
    "conj":   "conjunction",
    "(conj)": "conjunction",
    # preposition variants
    "prep":   "preposition",
    "(prep)": "preposition",
    # pronoun variants
    "pron":   "pronoun",
    "(pron)": "pronoun",
}

# Already-canonical values — leave them alone
CANONICAL = {"noun", "verb", "adjective", "adverb",
             "conjunction", "preposition", "pronoun"}


def _normalize_pos(raw: Optional[str]) -> Optional[str]:
    """Return canonical POS or None if unknown / already canonical."""
    if not raw:
        return None
    stripped = raw.strip()
    if stripped in CANONICAL:
        return None  # no change needed
    return POS_MAP.get(stripped)  # None if unknown variant


def _fix_study_items(conn: sqlite3.Connection) -> int:
    """Update extra_data JSON in study_items. Returns count of rows changed."""
    rows = conn.execute(
        "SELECT id, extra_data FROM study_items WHERE extra_data IS NOT NULL"
    ).fetchall()
    updated = 0
    for row_id, extra_raw in rows:
        try:
            data = json.loads(extra_raw)
        except (json.JSONDecodeError, TypeError):
            continue
        raw_pos = data.get("pos")
        canonical = _normalize_pos(raw_pos)
        if canonical is not None:
            data["pos"] = canonical
            conn.execute(
                "UPDATE study_items SET extra_data=? WHERE id=?",
                (json.dumps(data, ensure_ascii=False), row_id),
            )
            updated += 1
    return updated


def _fix_words(conn: sqlite3.Connection) -> int:
    """Update pos column in words table. Returns count of rows changed."""
    rows = conn.execute(
        "SELECT id, pos FROM words WHERE pos IS NOT NULL AND pos != ''"
    ).fetchall()
    updated = 0
    for row_id, raw_pos in rows:
        canonical = _normalize_pos(raw_pos)
        if canonical is not None:
            conn.execute(
                "UPDATE words SET pos=? WHERE id=?",
                (canonical, row_id),
            )
            updated += 1
    return updated


def run(db_path: Path = DB_PATH) -> None:
    if not Path(db_path).exists():
        print(f"057: DB not found at {db_path}; skipping.")
        return

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        si_count = _fix_study_items(conn) if "study_items" in tables else 0
        w_count  = _fix_words(conn)       if "words"       in tables else 0
        conn.commit()
        print(f"057: POS normalized — study_items: {si_count} rows, "
              f"words: {w_count} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
