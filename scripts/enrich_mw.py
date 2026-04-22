"""
scripts/enrich_mw.py — MW Elementary API로 단어 정의/발음/예문 보강
Section: Academy
Dependencies: backend/services/mw_api.py, MW_ELEMENTARY_API_KEY
API: none (CLI)

Usage:
    python3 scripts/enrich_mw.py              # 전체 684개 단어
    python3 scripts/enrich_mw.py --missing    # 정의 없는 단어만 재시도
    python3 scripts/enrich_mw.py --dry-run    # 처음 10개만 테스트

MW Elementary (sd2) 는 G3~5 수준. 684개 중 일부는 없을 수 있음.
없는 경우: definition 빈칸 유지 (프론트에서 "No entry" 표시)
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

# MW API 호출 간격 (초) — 초당 최대 2~3회 안전
DELAY = 0.4


# @tag ACADEMY
async def fetch_mw(word: str, client: httpx.AsyncClient) -> dict:
    """MW Elementary API 호출 → 파싱된 dict 반환.

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
        "all_defs":       shortdefs,          # 전체 정의 목록 (맥락별 선택용)
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
        print("❌ MW_ELEMENTARY_API_KEY 환경변수가 없습니다.")
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

    print(f"\n{'[dry-run] ' if dry_run else ''}MW Elementary 보강 시작 — {len(rows)}개 단어")
    if dry_run:
        print("(처음 10개만 테스트)\n")

    results = asyncio.run(enrich_all(rows, dry_run))

    # DB 저장
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
                json.dumps(r["all_defs"]),  # all_defs → synonyms_json 재활용 (임시)
                wid,
            ))
            hit += 1
        else:
            miss += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n── 결과 ──────────────────────")
    print(f"  ✅ MW 히트:     {hit}개")
    print(f"  ❌ 미등재:      {miss}개")
    print(f"  히트율:         {hit/(hit+miss)*100:.1f}%" if (hit+miss) else "")
    if not dry_run:
        print(f"  DB 업데이트 완료")
    else:
        print(f"  (dry-run — DB 미저장)")


if __name__ == "__main__":
    main()
