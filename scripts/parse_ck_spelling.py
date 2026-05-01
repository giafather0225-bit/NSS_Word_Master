#!/usr/bin/env python3
"""
parse_ck_spelling.py
Core Knowledge CKLA G3 Skills Workbook PDF (Unit 2-11)에서
Spelling 단어 목록을 파싱하여
data/ckla_source/spelling_words.json 으로 저장합니다.
라이선스: CC BY-NC-SA 3.0 (비상업적 교육 목적 사용)

PDF 구조:
  - 각 Spelling 주차마다 "Take-Home Worksheet" 페이지가 있음
  - 해당 페이지에 "Spelling Words" 헤더 포함
  - 다음 페이지에 번호 목록 (1. word 12. word 형태)
  - Challenge Words: "19. Challenge Word: give" 인라인
  - 단어 뒤 * 는 CVC 더블링 표시 (제거)
  - Unit 5, 6, 11: PDF 서버에서 제거됨 → 빈 데이터
"""

import json
import re
import io
import pathlib
import urllib.request
import time

OUT_PATH = pathlib.Path(__file__).parent.parent / "data" / "ckla_source" / "spelling_words.json"

WORKBOOK_URLS = {
    2: "https://www.coreknowledge.org/wp-content/uploads/2016/12/G3_U2_WB_SK_Rev-V1.pdf",
    3: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U3_WB_web.pdf",
    4: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U4_WB_web.pdf",
    5: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U5_WB_web.pdf",
    6: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U6_WB_web.pdf",
    7: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U7_WB_web.pdf",
    8: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U8_WB_web.pdf",
    9: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U9_WB_web.pdf",
    10: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U10_WB_web.pdf",
    11: "https://www.coreknowledge.org/wp-content/uploads/2017/01/CKLA_G3_U11_WB_web.pdf",
}

DOMAIN_MAP = {
    2: "Classification of Animals",
    3: "Human Body: Systems and Senses",
    4: "Ancient Roman Civilization",
    5: "Light and Sound",
    6: "The Vikings and Norse Mythology",
    7: "Astronomy: The Solar System and Beyond",
    8: "Native Americans",
    9: "European Exploration of North America",
    10: "Colonial America",
    11: "Ecology",
}

# Detect "Spelling Words" section header (appears on Take-Home Worksheet)
_SPELLING_WORDS_RE = re.compile(r"Spelling Words?\s*\n", re.IGNORECASE)

# Extract the spelling pattern description
_PATTERN_RE = re.compile(r"we are focusing on\s+([^.]+)\.", re.IGNORECASE)

# Match numbered word entries: "1. word*" and "19. Challenge Word: give"
_NUMBERED_RE = re.compile(
    r"(?:^|\s)(\d{1,2})\.\s+"
    r"(?:Challenge\s+Word:\s*([a-zA-Z]+)|([a-zA-Z][a-zA-Z\-\']*)\*?)"
    r"(?:\s+\([^)]*\))?",
)

# Standalone "Challenge Words, xxx and yyy" in description body
_CHALLENGE_INLINE_RE = re.compile(
    r"Challenge Words?,?\s+([a-zA-Z]+)\s+and\s+([a-zA-Z]+)",
    re.IGNORECASE,
)

# Inline "Challenge Word: answer" or "Challenge Word: great/grate" (homophone pair)
_CHALLENGE_WORD_RE = re.compile(
    r"Challenge\s+Word:\s*([a-zA-Z]+)(?:/([a-zA-Z]+))?",
    re.IGNORECASE,
)

# Spurious short common words that appear from worksheet prose
_SKIP_WORDS = frozenset({"challenge", "word", "the", "on", "in", "or", "to", "an", "be"})


def download_pdf(url: str) -> bytes:
    print(f"    Downloading: {url.split('/')[-1]}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except Exception as e:
        print(f"    [!] Download failed: {e}")
        return b""


def extract_pages(pdf_bytes: bytes) -> list[str]:
    """Return list of page text strings."""
    if not pdf_bytes:
        return []
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    except Exception:
        pass
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return []


def _parse_word_list(text: str) -> tuple[list[str], list[str]]:
    """Extract (words, challenge_words) from merged page text.

    "N. Challenge Word: xxx" → challenge list.
    All other numbered entries → word list (asterisks stripped).
    """
    words: list[str] = []
    challenges: list[str] = []

    for m in _NUMBERED_RE.finditer(text):
        if m.group(2):
            w = m.group(2).lower().strip()
            if w and w not in challenges:
                challenges.append(w)
        elif m.group(3):
            w = m.group(3).lower().strip()
            if w and len(w) >= 2 and w not in _SKIP_WORDS and w not in words:
                words.append(w)

    # Catch standalone "Challenge Word: answer" or "Challenge Word: great/grate"
    for m in _CHALLENGE_WORD_RE.finditer(text):
        for g in filter(None, (m.group(1), m.group(2))):
            w = g.lower()
            if w and w not in challenges:
                challenges.append(w)

    if not challenges:
        for m in _CHALLENGE_INLINE_RE.finditer(text):
            for g in (m.group(1).lower(), m.group(2).lower()):
                if g not in challenges:
                    challenges.append(g)

    return words, challenges


def _extract_pattern(text: str) -> str:
    m = _PATTERN_RE.search(text)
    return m.group(1).strip() if m else ""


def parse_unit(pages: list[str], unit: int) -> dict | None:
    """Find spelling word lists by locating 'Take-Home Worksheet' pages that
    also contain a 'Spelling Words' header, then merging with the next page
    where the actual numbered list lives."""
    word_list_pages: list[tuple[int, str]] = []
    seen: set[int] = set()

    for i, text in enumerate(pages):
        if i in seen:
            continue
        if "Take-Home Worksheet" in text and _SPELLING_WORDS_RE.search(text):
            next_text = pages[i + 1] if i + 1 < len(pages) else ""
            merged = text + "\n" + next_text
            words, _ = _parse_word_list(merged)
            if len(words) >= 5:
                word_list_pages.append((i, merged))
                seen.add(i)
                seen.add(i + 1)

    if not word_list_pages:
        return None

    result: dict = {"unit": unit, "domain": DOMAIN_MAP.get(unit, f"Unit {unit}")}
    for week_num, (page_idx, merged_text) in enumerate(word_list_pages[:4], start=1):
        pattern = _extract_pattern(merged_text)
        words, challenges = _parse_word_list(merged_text)
        result[f"week{week_num}"] = {
            "pattern": pattern,
            "words": words[:18],
            "challenge_words": challenges[:4],
        }

    return result if result.get("week1") else None


def _empty_weeks() -> dict:
    return {
        "week1": {"pattern": "", "words": [], "challenge_words": []},
        "week2": {"pattern": "", "words": [], "challenge_words": []},
        "week3": {"pattern": "", "words": [], "challenge_words": []},
    }


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results = []
    results.append({
        "unit": 1,
        "domain": "Classic Tales",
        "note": "No spelling instruction in Unit 1 (review unit)",
    })

    for unit_num in range(2, 12):
        print(f"\n[Unit {unit_num}]")

        url = WORKBOOK_URLS.get(unit_num)
        if not url:
            results.append({"unit": unit_num, "domain": DOMAIN_MAP.get(unit_num, ""),
                            "note": "No URL", **_empty_weeks()})
            continue

        pdf_bytes = download_pdf(url)
        time.sleep(0.3)

        if not pdf_bytes:
            results.append({
                "unit": unit_num,
                "domain": DOMAIN_MAP.get(unit_num, f"Unit {unit_num}"),
                "note": "PDF not available — manual entry required",
                **_empty_weeks(),
            })
            print("    PDF not available")
            continue

        pages = extract_pages(pdf_bytes)
        print(f"    Pages: {len(pages)}, text: {sum(len(p) for p in pages):,} chars")

        parsed = parse_unit(pages, unit_num)

        if parsed:
            results.append(parsed)
            weeks = [k for k in parsed if k.startswith("week")]
            for w in sorted(weeks):
                d = parsed[w]
                print(f"    {w}: {len(d['words'])} words {d['words'][:4]} | challenge: {d['challenge_words']}")
        else:
            results.append({
                "unit": unit_num,
                "domain": DOMAIN_MAP.get(unit_num, f"Unit {unit_num}"),
                "note": "Parsing failed — manual entry required",
                **_empty_weeks(),
            })
            print("    FAIL — manual entry required")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Saved: {OUT_PATH} ({len(results)} units)")
    print("\n=== Summary ===")
    for r in results:
        u = r.get("unit")
        note = r.get("note", "")
        if note:
            print(f"  Unit {u:2d}: {note}")
        else:
            total = sum(len(r.get(f"week{w}", {}).get("words", [])) for w in range(1, 5))
            weeks = len([k for k in r if k.startswith("week")])
            print(f"  Unit {u:2d}: OK  {weeks} weeks, {total} words")


if __name__ == "__main__":
    main()
