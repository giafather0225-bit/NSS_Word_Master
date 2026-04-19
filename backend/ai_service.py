"""하이브리드 AI 서비스 — Ollama(로컬) 우선, Gemini(클라우드) 폴백.

라우팅 규칙
───────────
항상 Ollama 먼저 시도:
  1. JSON 파싱 성공  → 품질 점수 계산
  2. 품질 점수 ≥ 0.55 → Ollama 결과 반환
  3. 품질 점수  < 0.55 → Gemini로 재시도
  4. Ollama 타임아웃·오류 → Gemini로 즉시 재시도

Gemini를 직접 사용하는 경우:
  - 입력 텍스트 > LONG_TEXT_THRESHOLD 글자 (복잡한 문맥)
  - 호출 시 force_gemini=True 전달

환경 변수 (.env):
  GEMINI_API_KEY  — Gemini REST API 키
  OLLAMA_HOST     — Ollama 서버 URL (기본 http://127.0.0.1:11434)
  OLLAMA_OCR_MODEL — 텍스트 정제 모델 (기본 gemma2:2b)
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

from backend.utils import parse_json_array, strip_json_fences

load_dotenv()

log = logging.getLogger(__name__)

# ── 설정 ─────────────────────────────────────────────────────────
OLLAMA_HOST      = os.environ.get("OLLAMA_HOST",      "http://127.0.0.1:11434")
OLLAMA_OCR_MODEL = os.environ.get("OLLAMA_OCR_MODEL", "gemma2:2b")
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY",   "")
GEMINI_MODEL     = "gemini-1.5-flash"
GEMINI_ENDPOINT  = (
    "https://generativelanguage.googleapis.com/v1/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# 이 길이 초과 시 Gemini 직행 (복잡한 문맥 처리)
LONG_TEXT_THRESHOLD = 3_000
# Ollama 품질 점수가 이 값 미만이면 Gemini로 폴백
QUALITY_THRESHOLD = 0.55


# ══════════════════════════════════════════════════════════════════
# 공통 유틸
# ══════════════════════════════════════════════════════════════════

def _normalize_entry(e: dict) -> dict:
    """각 항목의 필드를 string으로 정규화."""
    return {
        "word":       (e.get("word")       or "").strip(),
        "pos":        (e.get("pos")        or "").strip(),
        "definition": (e.get("definition") or "").strip(),
        "example":    (e.get("example")    or "").strip(),
    }


def quality_score(entries: list[dict]) -> float:
    """0.0 ~ 1.0 품질 점수.

    채점 기준 (항목별):
    - definition 길이 < 8       → 0.0 (사실상 없음)
    - definition 이 word 로 시작 → 0.3 (단순 반복)
    - example 에 word 포함      → +0.4 보너스
    - 그 외                     → 0.6
    """
    if not entries:
        return 0.0
    scores: list[float] = []
    for e in entries:
        word = e.get("word", "").strip().lower()
        defn = e.get("definition", "").strip()
        ex   = e.get("example",   "").strip().lower()

        if len(defn) < 8:
            scores.append(0.0)
            continue
        base = 0.3 if defn.lower().startswith(word) else 0.6
        bonus = 0.4 if (word and word in ex) else 0.0
        scores.append(min(base + bonus, 1.0))

    return sum(scores) / len(scores)


# ══════════════════════════════════════════════════════════════════
# Ollama 레이어
# ══════════════════════════════════════════════════════════════════

_REFINE_PROMPT = """You are a STRICT vocabulary extractor for a Korean kids' English textbook (Voca 8000).

The textbook format is:
  word (pos)        definition text
                    [Example sentence in brackets.]

Raw OCR text from a scanned page:
\"\"\"
{ocr_text}
\"\"\"

STRICT RULES:
1. Extract ONLY vocabulary entries that appear in the textbook. Do NOT invent or add extra words.
2. Each entry has: word, part of speech in parentheses, a definition, and an example in [brackets].
3. Copy the definition and example EXACTLY as written in the textbook. Do NOT rephrase or modify.
4. If an example sentence is in [brackets], extract it WITHOUT the brackets.
5. Skip headers like "Voca 8000", "Words in English", "Lesson X", page numbers.
6. Skip check marks, stars, or other symbols next to words.
7. Each page typically has about 5 words. Do NOT extract more words than actually exist.
8. If a word like "upside down" has a space, keep it as-is.

Return ONLY a valid JSON array. Each object must have exactly these 4 keys:
  "word"       - the vocabulary word exactly as printed
  "pos"        - part of speech (e.g. "adv", "n", "adj", "v") without parentheses or periods
  "definition" - the definition exactly as written in the textbook
  "example"    - the example sentence exactly as written, without brackets

Example output:
[
  {{"word": "upside down", "pos": "adv", "definition": "having the part that is usually at the top turned to be at the bottom", "example": "The box was lying on the floor upside down."}},
  {{"word": "beak", "pos": "n", "definition": "the hard curved or pointed parts of the mouth of birds", "example": "He avoided the goose's beak and ran away."}}
]

No markdown fences, no extra text, no explanation. JSON array only.
"""

_ENRICH_PROMPT = """\
You are a helpful English vocabulary creator for kids.

For each word below, provide a short English definition and one example sentence.

Input JSON:
{words_json}

Return a JSON array with objects having exactly: word, pos, definition, example.
No markdown, no extra text.
"""

_EXAMPLE_PROMPT = """\
Write one short, natural English example sentence for a kid using the word "{word}" ({pos}).
Definition: {definition}

Reply with ONLY the sentence, no quotes, no explanation.
"""


async def _ollama_chat(prompt: str, model: str | None = None, timeout: float = 90.0) -> str:
    """Ollama /api/chat 호출 → 응답 문자열 반환."""
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    payload = {
        "model":   model or OLLAMA_OCR_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":  False,
        "options": {"temperature": 0.1},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return (resp.json().get("message", {}).get("content") or "").strip()


# ══════════════════════════════════════════════════════════════════
# Gemini 레이어
# ══════════════════════════════════════════════════════════════════

async def _gemini_generate(prompt: str, timeout: float = 60.0) -> str:
    """Gemini REST API 호출 → 응답 문자열 반환."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 미설정 — .env 파일을 확인하세요.")
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                GEMINI_ENDPOINT,
                json=body,
                headers={"x-goog-api-key": GEMINI_API_KEY},
            )
            resp.raise_for_status()
        except Exception as exc:
            log.warning("Gemini request failed: %s", type(exc).__name__)
            raise RuntimeError(f"Gemini request failed: {type(exc).__name__}") from None
        candidates = resp.json().get("candidates", [])
        if not candidates:
            raise ValueError("Gemini 응답에 candidates 없음")
        parts = candidates[0].get("content", {}).get("parts", [])
        return (parts[0].get("text") or "").strip() if parts else ""


# ══════════════════════════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════════════════════════

async def refine_ocr_text(
    ocr_text: str,
    *,
    force_gemini: bool = False,
) -> tuple[list[dict], str]:
    """OCR raw text → 정제된 단어 목록.

    Returns:
        (entries, provider) — provider: "ollama" | "gemini"

    동작:
        1. 텍스트가 LONG_TEXT_THRESHOLD 초과이거나 force_gemini=True → Gemini 직행
        2. Ollama 시도 → 품질 점수 ≥ QUALITY_THRESHOLD → 반환
        3. 품질 미달 or 오류 → Gemini 재시도
    """
    prompt = _REFINE_PROMPT.format(ocr_text=ocr_text[:5_000])
    use_gemini_first = force_gemini or (len(ocr_text) > LONG_TEXT_THRESHOLD)

    if not use_gemini_first:
        try:
            raw = await _ollama_chat(prompt, timeout=120.0)
            entries = parse_json_array(raw)
            if entries is not None:
                normalized = [_normalize_entry(e) for e in entries if e.get("word")]
                score = quality_score(normalized)
                log.debug("Ollama quality score: %.2f (%d entries)", score, len(normalized))
                if score >= QUALITY_THRESHOLD:
                    return normalized, "ollama"
                log.info("Ollama quality %.2f < threshold %.2f — falling back to Gemini",
                         score, QUALITY_THRESHOLD)
            else:
                log.info("Ollama returned non-JSON — falling back to Gemini")
        except Exception as exc:
            log.warning("Ollama error: %s — falling back to Gemini", exc)

    # Gemini 폴백 (또는 직행)
    provider = "gemini"
    raw = await _gemini_generate(prompt)
    entries = parse_json_array(raw)
    if entries is None:
        raise ValueError(f"Gemini 응답을 JSON으로 파싱 실패:\n{raw[:400]}")
    normalized = [_normalize_entry(e) for e in entries if e.get("word")]
    if not normalized:
        raise ValueError("정제 결과에 유효한 단어 항목 없음")
    return normalized, provider


async def enrich_words(
    words: list[dict],
    *,
    force_gemini: bool = False,
) -> tuple[list[dict], str]:
    """단어 목록에 definition + example 채우기 (word + pos 만 있는 경우).

    Returns:
        (enriched_entries, provider)
    """
    payload = [{"word": e.get("word", ""), "pos": e.get("pos", "")} for e in words[:80]]
    prompt  = _ENRICH_PROMPT.format(words_json=json.dumps(payload, ensure_ascii=False))

    if not force_gemini:
        try:
            raw = await _ollama_chat(prompt, timeout=90.0)
            entries = parse_json_array(raw)
            if entries:
                normalized = [_normalize_entry(e) for e in entries if e.get("word")]
                if quality_score(normalized) >= QUALITY_THRESHOLD:
                    return normalized, "ollama"
        except Exception as exc:
            log.warning("Ollama enrich error: %s — falling back to Gemini", exc)

    raw = await _gemini_generate(prompt)
    entries = parse_json_array(raw)
    if not entries:
        raise ValueError("Gemini enrich 파싱 실패")
    return [_normalize_entry(e) for e in entries if e.get("word")], "gemini"


async def generate_example(
    word: str,
    definition: str,
    pos: str = "",
    *,
    force_gemini: bool = False,
) -> tuple[str, str]:
    """단어에 대한 예문 한 문장 생성.

    Returns:
        (example_sentence, provider)
    """
    prompt = _EXAMPLE_PROMPT.format(word=word, pos=pos or "—", definition=definition)

    if not force_gemini:
        try:
            sentence = await _ollama_chat(prompt, timeout=30.0)
            sentence = sentence.strip().strip('"\'')
            if len(sentence) > 10 and word.lower() in sentence.lower():
                return sentence, "ollama"
            log.info("Ollama example quality low for '%s' — trying Gemini", word)
        except Exception as exc:
            log.warning("Ollama example error for '%s': %s", word, exc)

    sentence = await _gemini_generate(prompt)
    return sentence.strip().strip('"\''), "gemini"


async def smart_refine(
    ocr_text: str,
) -> dict[str, Any]:
    """단일 진입점: OCR 텍스트 → 완전한 단어 목록.

    내부적으로 refine_ocr_text → (필요시) enrich_words 를 순서대로 호출.

    Returns:
        {
          "entries":   list[dict],   # word/pos/definition/example
          "providers": list[str],    # 각 단계에서 사용된 provider
          "quality":   float,        # 최종 품질 점수
        }
    """
    entries, p1 = await refine_ocr_text(ocr_text)
    providers = [p1]

    # definition/example 이 전부 비어있으면 enrich
    needs_enrich = all(
        not e.get("definition") and not e.get("example")
        for e in entries
    )
    if needs_enrich:
        entries, p2 = await enrich_words(entries)
        providers.append(p2)

    return {
        "entries":   entries,
        "providers": providers,
        "quality":   quality_score(entries),
    }
