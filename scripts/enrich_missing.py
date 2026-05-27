"""
scripts/enrich_missing.py — fill in 78 words missing from MW
Section: Academy
Dependencies: MW_ELEMENTARY_API_KEY, nltk (wordnet)
API: none (CLI)

Strategy:
  A. transform the word form and retry MW
     (fertilizes → fertilize, calcified → calcify, axial bones → axial)
  B. if still missing, fall back to WordNet (NLTK)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

import httpx
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

DB_PATH    = Path.home() / "NSS_Learning" / "database" / "voca.db"
MW_API_KEY = os.environ.get("MW_ELEMENTARY_API_KEY", "")
MW_BASE    = "https://www.dictionaryapi.com/api/v3/references/sd2/json"
DELAY      = 0.4
lemmatizer = WordNetLemmatizer()


# @tag ACADEMY
def lemmatize_word(word: str) -> list[str]:
    """Return various base-form candidates for a word (deduped, original excluded)."""
    word = word.strip().lower()
    candidates = []

    # compound word: try the first word only ("axial bones" → "axial")
    parts = word.split()
    if len(parts) > 1:
        candidates.append(parts[0])          # first word
        candidates.append(" ".join(parts[:2]))  # first two words

    # lemma per part of speech
    for pos in ("v", "n", "a", "r"):
        lem = lemmatizer.lemmatize(word, pos=pos)
        if lem != word:
            candidates.append(lem)

    # general rules (-ly, -tion, -ed, -ing, -izes/-ise)
    for suffix, replacement in [
        ("izes", "ize"), ("ising", "ise"), ("ified", "ify"),
        ("ification", "ify"), ("edly", "ed"), ("ingly", "ing"),
        ("ness", ""), ("ly", ""), ("tion", ""), ("ment", ""),
    ]:
        if word.endswith(suffix) and len(word) - len(suffix) > 3:
            candidates.append(word[: -len(suffix)] + replacement)

    # dedupe, exclude the original
    seen = {word}
    out = []
    for c in candidates:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


# @tag ACADEMY
async def fetch_mw(word: str, client: httpx.AsyncClient) -> dict | None:
    """Query MW. Returns a dict on hit, None if not found."""
    try:
        r = await client.get(f"{MW_BASE}/{word}", params={"key": MW_API_KEY}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    if not data or not isinstance(data, list) or isinstance(data[0], str):
        return None

    entry    = data[0]
    shortdefs = entry.get("shortdef", [])
    if not shortdefs:
        return None

    def _audio(e):
        try:
            af = e["hwi"]["prs"][0]["sound"]["audio"]
            sub = ("bix" if af.startswith("bix") else
                   "gg"  if af.startswith("gg") else
                   "number" if (af[0].isdigit() or af[0] == "_") else af[0])
            return f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{sub}/{af}.mp3"
        except Exception:
            return ""

    def _example(e):
        try:
            for d in e.get("def", []):
                for sseq in d.get("sseq", []):
                    for sense in sseq:
                        if isinstance(sense, list) and sense[0] == "sense":
                            for item in sense[1].get("dt", []):
                                if isinstance(item, list) and item[0] == "vis":
                                    t = item[1][0].get("t", "")
                                    if t:
                                        return re.sub(r"\{[^}]+\}", "", t).strip()
        except Exception:
            pass
        return ""

    return {
        "source":         "mw",
        "definition":     shortdefs[0],
        "all_defs":       shortdefs,
        "part_of_speech": entry.get("fl", ""),
        "audio_url":      _audio(entry),
        "example_1":      _example(entry),
    }


# @tag ACADEMY
def wordnet_lookup(word: str) -> dict | None:
    """Get the definition of the first synset from WordNet."""
    # convert compound words to underscores
    wn_word = word.replace(" ", "_").replace("-", "_")
    synsets = wordnet.synsets(wn_word)
    if not synsets:
        # retry with the first word
        synsets = wordnet.synsets(word.split()[0])
    if not synsets:
        return None

    syn  = synsets[0]
    defn = syn.definition()
    pos_map = {"n": "noun", "v": "verb", "a": "adjective",
               "s": "adjective", "r": "adverb"}
    pos  = pos_map.get(syn.pos(), "")

    # example sentence
    examples = syn.examples()
    example  = examples[0] if examples else ""

    return {
        "source":         "wordnet",
        "definition":     defn,
        "all_defs":       [defn],
        "part_of_speech": pos,
        "audio_url":      "",       # WordNet has no audio
        "example_1":      example,
    }


# @tag ACADEMY @tag SYSTEM
async def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    missing = conn.execute("""
        SELECT id, word FROM us_academy_words
        WHERE domain_num IS NOT NULL
          AND (definition IS NULL OR definition = '')
        ORDER BY id
    """).fetchall()

    print(f"\nStarting to fill in {len(missing)} words missing from MW\n")
    print(f"  {'word':<25} {'strategy':<10} {'result'}")
    print(f"  {'-'*25} {'-'*10} {'-'*55}")

    stats = {"mw_retry": 0, "wordnet": 0, "still_missing": 0}

    async with httpx.AsyncClient() as client:
        for wid, word in missing:
            result = None
            strategy = "-"

            # ── A. retry MW (transformed candidates) ────────────────────
            candidates = lemmatize_word(word)
            for cand in candidates:
                result = await fetch_mw(cand, client)
                await asyncio.sleep(DELAY)
                if result:
                    strategy = f"MW({cand})"
                    stats["mw_retry"] += 1
                    break

            # ── B. WordNet fallback ─────────────────────────────────────
            if not result:
                result = wordnet_lookup(word)
                if result:
                    strategy = "WordNet"
                    stats["wordnet"] += 1

            if not result:
                stats["still_missing"] += 1
                print(f"  ❌ {word:<25} {'none':<10}")
                continue

            # update DB
            src_tag = f"[{result['source']}] " if result["source"] == "wordnet" else ""
            conn.execute("""
                UPDATE us_academy_words SET
                    definition     = ?,
                    part_of_speech = ?,
                    audio_url      = ?,
                    example_1      = ?,
                    synonyms_json  = ?
                WHERE id = ?
            """, (
                src_tag + result["definition"],
                result["part_of_speech"],
                result["audio_url"],
                result["example_1"],
                json.dumps(result["all_defs"]),
                wid,
            ))

            icon = "✅" if result["source"] == "mw" else "🔵"
            print(f"  {icon} {word:<25} {strategy:<12} {result['definition'][:50]}")

    conn.commit()
    conn.close()

    print(f"\n── Results ───────────────────────────────")
    print(f"  ✅ MW retry success:  {stats['mw_retry']}")
    print(f"  🔵 WordNet filled:    {stats['wordnet']}")
    print(f"  ❌ still missing:     {stats['still_missing']}")
    total_covered = stats['mw_retry'] + stats['wordnet']
    print(f"  filled this run:      {total_covered}")


if __name__ == "__main__":
    if not MW_API_KEY:
        print("❌ MW_ELEMENTARY_API_KEY not set"); sys.exit(1)
    asyncio.run(main())
