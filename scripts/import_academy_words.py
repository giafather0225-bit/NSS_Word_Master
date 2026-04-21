"""
scripts/import_academy_words.py — 300단어 시드 데이터 → DB 저장
                                   + MW API / WordNet 데이터 보강
Section: Academy
Dependencies: services/mw_api.py, services/wordnet_service.py
API: none (run directly)

Usage:
    # 기본 (WordNet만, MW API 키 없이):
    python3 scripts/import_academy_words.py

    # MW API 키 포함:
    MW_ELEMENTARY_API_KEY=your_key python3 scripts/import_academy_words.py

    # 이미 임포트된 경우 강제 재임포트:
    python3 scripts/import_academy_words.py --force
"""

import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.academy.words_seed import WORDS
from services.wordnet_service import get_synonyms_antonyms_json

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag ACADEMY
async def enrich_with_mw(word: str) -> dict:
    """Try MW API. Return empty dict if API key not set or request fails."""
    try:
        from services.mw_api import fetch_word, MW_API_KEY
        if not MW_API_KEY:
            return {}
        return await fetch_word(word)
    except Exception:
        return {}


# @tag ACADEMY
async def import_words(force: bool = False) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    existing = conn.execute(
        "SELECT COUNT(*) FROM us_academy_words"
    ).fetchone()[0]

    if existing > 0 and not force:
        print(f"[import_words] {existing} words already in DB. Use --force to reimport.")
        conn.close()
        return

    if force:
        conn.execute("DELETE FROM us_academy_words")
        conn.commit()
        print("[import_words] Cleared existing words.")

    total   = len(WORDS)
    success = 0

    for i, entry in enumerate(WORDS, 1):
        word, level, category, sort_order, morphology, word_family = entry

        # WordNet — always available
        try:
            syn_json, ant_json = get_synonyms_antonyms_json(word, max_each=5)
        except Exception:
            syn_json, ant_json = "[]", "[]"

        # MW API — optional (needs API key)
        mw = await enrich_with_mw(word)
        definition     = mw.get("definition", "")
        part_of_speech = mw.get("part_of_speech", "")
        audio_url      = mw.get("audio_url", "")
        example_1      = mw.get("example_1", "")

        conn.execute(
            """INSERT INTO us_academy_words
               (word, level, category, sort_order,
                definition, part_of_speech, audio_url, example_1,
                synonyms_json, antonyms_json,
                morphology, word_family, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (word, level, category, sort_order,
             definition, part_of_speech, audio_url, example_1,
             syn_json, ant_json,
             morphology, word_family),
        )
        success += 1

        if i % 10 == 0:
            conn.commit()
            print(f"[import_words] {i}/{total} done...")
        time.sleep(0.05)  # gentle rate limit for MW API

    conn.commit()
    conn.close()
    print(f"[import_words] Imported {success}/{total} words.")
    if success < total:
        print("[import_words] Some words failed — check logs above.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(import_words(force=force))
