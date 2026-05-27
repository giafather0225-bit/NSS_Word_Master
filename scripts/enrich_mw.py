"""
scripts/enrich_mw.py — enrich word definitions/pronunciation/examples via the MW Elementary API
Section: Academy
Dependencies: backend/services/mw_api.py, MW_ELEMENTARY_API_KEY
API: none (CLI)

Usage:
    python3 scripts/enrich_mw.py              # all 684 words
    python3 scripts/enrich_mw.py --missing    # retry only words without a definition
    python3 scripts/enrich_mw.py --dry-run    # test the first 10 only

MW Elementary (sd2) is at a G3-5 level. Some of the 684 may be missing.
When missing: leave definition blank (frontend shows "No entry")
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
from pathlib import Path

import httpx

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

MW_API_KEY  = os.environ.get("MW_ELEMENTARY_API_KEY", "")
MW_BASE_URL = "https://www.dictionaryapi.com/api/v3/references/sd2/json"

# MW API call interval (sec) — safe at up to 2-3 calls/sec
DELAY = 0.4


# @tag ACADEMY
async def fetch_mw(word: str, client: httpx.AsyncClient) -> dict:
    """Call the MW Elementary API → return a parsed dict.

    Returns keys: definition, all_defs (list), part_of_speech,
                  audio_url, example_1, found (bool)
    """
    try:
        resp = await client.get(
            f"{MW_BASE_URL}/{word}",
            params={"key": MW_API_KEY},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"found": False, "error": str(e)}

    if not data or not isinstance(data, list) or isinstance(data[0], str):
        return {"found": False, "error": "no entry"}

    entry = data[0]
    shortdefs = entry.get("shortdef", [])

    return {
        "found":          bool(shortdefs),
        "definition":     shortdefs[0] if shortdefs else "",
        "all_defs":       shortdefs,          # full list of definitions (for context-based selection)
        "part_of_speech": entry.get("fl", ""),
        "audio_url":      _audio_url(entry),
        "example_1":      _example(entry),
    }


# @tag ACADEMY
def _audio_url(entry: dict) -> str:
    try:
        af = entry["hwi"]["prs"][0]["sound"]["audio"]
        if af.startswith("bix"):    sub = "bix"
        elif af.startswith("gg"):   sub = "gg"
        elif af[0].isdigit() or af[0] == "_": sub = "number"
        else:                       sub = af[0]
        return f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{sub}/{af}.mp3"
    except Exception:
        return ""


# @tag ACADEMY
def _example(entry: dict) -> str:
    try:
        for d in entry.get("def", []):
            for sseq in d.get("sseq", []):
                for sense in sseq:
                    if isinstance(sense, list) and sense[0] == "sense":
                        for item in sense[1].get("dt", []):
                            if isinstance(item, list) and item[0] == "vis":
                                t = item[1][0].get("t", "")
                                if t:
                                    import re
                                    return re.sub(r"\{[^}]+\}", "", t).strip()
    except Exception:
        pass
    return ""


# @tag ACADEMY
async def enrich_all(words: list[tuple], dry_run: bool) -> dict:
    """words: [(id, word), ...] → {id: fetch_result}"""
    results = {}
    async with httpx.AsyncClient() as client:
        for i, (wid, word) in enumerate(words):
            if dry_run and i >= 10:
                break
            result = await fetch_mw(word, client)
            results[wid] = (word, result)
            status = "✅" if result.get("found") else "❌"
            defn   = result.get("definition", result.get("error", ""))[:55]
            print(f"  {status} {word:<22} {defn}")
            await asyncio.sleep(DELAY)
    return results


# @tag ACADEMY @tag SYSTEM
def main() -> None:
    if not MW_API_KEY:
        print("❌ MW_ELEMENTARY_API_KEY environment variable is not set.")
        print("   export MW_ELEMENTARY_API_KEY=your-key-here")
        sys.exit(1)

    dry_run    = "--dry-run" in sys.argv
    only_miss  = "--missing" in sys.argv

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    if only_miss:
        rows = conn.execute(
            "SELECT id, word FROM us_academy_words "
            "WHERE domain_num IS NOT NULL "
            "AND (definition IS NULL OR definition = '') "
            "ORDER BY id"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, word FROM us_academy_words "
            "WHERE domain_num IS NOT NULL "
            "ORDER BY id"
        ).fetchall()

    print(f"\n{'[dry-run] ' if dry_run else ''}Starting MW Elementary enrichment — {len(rows)} words")
    if dry_run:
        print("(testing the first 10 only)\n")

    results = asyncio.run(enrich_all(rows, dry_run))

    # Save to DB
    hit = miss = 0
    for wid, (word, r) in results.items():
        if r.get("found"):
            conn.execute("""
                UPDATE us_academy_words SET
                    definition     = ?,
                    part_of_speech = ?,
                    audio_url      = ?,
                    example_1      = ?,
                    synonyms_json  = ?
                WHERE id = ?
            """, (
                r["definition"],
                r["part_of_speech"],
                r["audio_url"],
                r["example_1"],
                json.dumps(r["all_defs"]),  # all_defs → reuse synonyms_json (temporary)
                wid,
            ))
            hit += 1
        else:
            miss += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n── Results ──────────────────────")
    print(f"  ✅ MW hits:     {hit}")
    print(f"  ❌ not found:   {miss}")
    print(f"  hit rate:       {hit/(hit+miss)*100:.1f}%" if (hit+miss) else "")
    if not dry_run:
        print(f"  DB update complete")
    else:
        print(f"  (dry-run — DB not saved)")


if __name__ == "__main__":
    main()
