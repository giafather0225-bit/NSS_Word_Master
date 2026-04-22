"""
scripts/enrich_missing.py — MW 미등재 78개 보완
Section: Academy
Dependencies: MW_ELEMENTARY_API_KEY, nltk (wordnet)
API: none (CLI)

전략:
  A. 단어 형태 변환 후 MW 재시도
     (fertilizes → fertilize, calcified → calcify, axial bones → axial)
  B. 여전히 없으면 WordNet(NLTK) 폴백
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
    """단어의 다양한 기본형 후보 반환 (중복 제거, 원형 제외)."""
    word = word.strip().lower()
    candidates = []

    # 복합어: 첫 단어만 시도 ("axial bones" → "axial")
    parts = word.split()
    if len(parts) > 1:
        candidates.append(parts[0])          # 첫 단어
        candidates.append(" ".join(parts[:2]))  # 두 단어

    # 품사별 lemma
    for pos in ("v", "n", "a", "r"):
        lem = lemmatizer.lemmatize(word, pos=pos)
        if lem != word:
            candidates.append(lem)

    # 일반 규칙 (-ly, -tion, -ed, -ing, -izes/-ise)
    for suffix, replacement in [
        ("izes", "ize"), ("ising", "ise"), ("ified", "ify"),
        ("ification", "ify"), ("edly", "ed"), ("ingly", "ing"),
        ("ness", ""), ("ly", ""), ("tion", ""), ("ment", ""),
    ]:
        if word.endswith(suffix) and len(word) - len(suffix) > 3:
            candidates.append(word[: -len(suffix)] + replacement)

    # 중복 제거, 원형 제외
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
    """MW 조회. 히트하면 dict, 미등재면 None."""
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
    """WordNet에서 첫 번째 synset 정의 가져오기."""
    # 복합어는 언더스코어로 변환
    wn_word = word.replace(" ", "_").replace("-", "_")
    synsets = wordnet.synsets(wn_word)
    if not synsets:
        # 첫 단어로 재시도
        synsets = wordnet.synsets(word.split()[0])
    if not synsets:
        return None

    syn  = synsets[0]
    defn = syn.definition()
    pos_map = {"n": "noun", "v": "verb", "a": "adjective",
               "s": "adjective", "r": "adverb"}
    pos  = pos_map.get(syn.pos(), "")

    # 예문
    examples = syn.examples()
    example  = examples[0] if examples else ""

    return {
        "source":         "wordnet",
        "definition":     defn,
        "all_defs":       [defn],
        "part_of_speech": pos,
        "audio_url":      "",       # WordNet은 오디오 없음
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

    print(f"\nMW 미등재 {len(missing)}개 보완 시작\n")
    print(f"  {'단어':<25} {'전략':<10} {'결과'}")
    print(f"  {'-'*25} {'-'*10} {'-'*55}")

    stats = {"mw_retry": 0, "wordnet": 0, "still_missing": 0}

    async with httpx.AsyncClient() as client:
        for wid, word in missing:
            result = None
            strategy = "-"

            # ── A. MW 재시도 (변형 후보들) ──────────────────────────────
            candidates = lemmatize_word(word)
            for cand in candidates:
                result = await fetch_mw(cand, client)
                await asyncio.sleep(DELAY)
                if result:
                    strategy = f"MW({cand})"
                    stats["mw_retry"] += 1
                    break

            # ── B. WordNet 폴백 ──────────────────────────────────────────
            if not result:
                result = wordnet_lookup(word)
                if result:
                    strategy = "WordNet"
                    stats["wordnet"] += 1

            if not result:
                stats["still_missing"] += 1
                print(f"  ❌ {word:<25} {'없음':<10}")
                continue

            # DB 업데이트
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

    print(f"\n── 결과 ───────────────────────────────")
    print(f"  ✅ MW 재시도 성공:  {stats['mw_retry']}개")
    print(f"  🔵 WordNet 보완:    {stats['wordnet']}개")
    print(f"  ❌ 여전히 미등재:   {stats['still_missing']}개")
    total_covered = stats['mw_retry'] + stats['wordnet']
    print(f"  이번 보완 성공:    {total_covered}개")


if __name__ == "__main__":
    if not MW_API_KEY:
        print("❌ MW_ELEMENTARY_API_KEY 없음"); sys.exit(1)
    asyncio.run(main())
