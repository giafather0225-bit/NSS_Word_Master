"""
NSS Word Master — Vision LLM Direct Extraction Pipeline v2.
============================================================
Single-pass: image → Vision LLM → structured JSON.

WHY THIS DESIGN:
  The old pipeline (image → OCR text → LLM structuring) destroyed spatial
  layout information. When OCR flattened the page to text, the positional
  relationship between a word and its definition was lost. If even one word
  was missed, ALL subsequent word-definition pairs shifted by one position.

  Vision LLMs see the image directly and extract each word WITH its adjacent
  definition as an atomic unit, preventing the shift bug entirely.

FALLBACK CHAIN:
  1. Gemini 2.0 Flash (cloud) — fastest, highest accuracy
  2. qwen2.5vl:3b via Ollama (local) — M1 8GB compatible, no network needed
  3. macOS Vision OCR + gemma2:2b (legacy) — text-based fallback

STRUCTURED OUTPUT:
  Uses Ollama's format parameter with a JSON schema to enforce output shape.
  This eliminates markdown fences, parsing errors, and format inconsistencies.
"""

import asyncio
import base64
import json
import logging
import os
import re
import tempfile
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────
_OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash"
    ":generateContent"
)

HEIC_EXTENSIONS = {".heic", ".heif"}
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"
} | HEIC_EXTENSIONS

# ── JSON Schema for Ollama Structured Output ────────────────────
# Ollama's `format` parameter constrains the model to output ONLY
# valid JSON matching this schema. No markdown, no extra text.
_VOCAB_SCHEMA = {
    "type": "object",
    "properties": {
        "words": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "word":       {"type": "string"},
                    "pos":        {"type": "string"},
                    "definition": {"type": "string"},
                    "example":    {"type": "string"}
                },
                "required": ["word", "pos", "definition", "example"]
            }
        }
    },
    "required": ["words"]
}

# ── Extraction prompt (shared by Gemini and Ollama) ─────────────
_EXTRACT_PROMPT = """You are an expert OCR assistant for English vocabulary textbooks.

Look at this textbook page image. Extract ALL English vocabulary entries.

CRITICAL RULES:
1. Each word MUST be paired with ITS OWN definition visible next to it on the page.
   Do NOT shift or swap definitions between words.
2. This textbook uses THIN PAPER — ignore any faint bleed-through text from the reverse side.
3. Extract the EXACT definition and example sentence printed in the textbook.
4. Skip headers, page numbers, lesson titles, copyright notices, and review sections.
5. Clean up OCR artifacts: remove leading V, ✓, *, numbers, etc. from words.
6. Words must be lowercase. Part of speech abbreviated: n, v, adj, adv, conj, prep.
7. Example sentences must not include brackets [ ].
8. If a definition is partially unreadable, write what you can see.

SELF-CHECK before output:
- Does each definition actually describe the meaning of its paired word?
- Does each example sentence use the vocabulary word?
- Typical count: 6-10 words per page. If you found fewer than 5, look again.

Return a JSON object: {"words": [{"word": "...", "pos": "...", "definition": "...", "example": "..."}]}"""


# ── Image Helpers ───────────────────────────────────────────────

async def _convert_to_jpeg(image_path: Path) -> Path:
    """Convert HEIC or other formats to JPEG via macOS sips."""
    if image_path.suffix.lower() in (".jpg", ".jpeg"):
        return image_path
    tmp_dir = Path(tempfile.mkdtemp())
    jpeg_path = tmp_dir / (image_path.stem + ".jpg")
    proc = await asyncio.create_subprocess_exec(
        "sips", "-s", "format", "jpeg", str(image_path), "--out", str(jpeg_path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"sips conversion failed: {stderr.decode()}")
    return jpeg_path


def _image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# ── Strategy 1: Gemini 2.0 Flash ───────────────────────────────

async def _extract_via_gemini(b64_image: str, mime: str = "image/jpeg") -> list[dict] | None:
    """Cloud extraction via Gemini. Returns vocab list or None on failure."""
    if not _GEMINI_KEY:
        return None

    payload = {
        "contents": [{
            "parts": [
                {"text": _EXTRACT_PROMPT},
                {"inline_data": {"mime_type": mime, "data": b64_image}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{_GEMINI_URL}?key={_GEMINI_KEY}", json=payload
            )
            if resp.status_code == 429:
                log.warning("Gemini 429 rate-limited, will try local model")
                return None
            resp.raise_for_status()

        result = resp.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        words = data.get("words", data) if isinstance(data, dict) else data
        if isinstance(words, list) and words:
            log.info("Gemini extracted %d words", len(words))
            return _normalize(words)
    except Exception as e:
        log.warning("Gemini extraction failed: %s", e)
    return None


# ── Strategy 2: Ollama Vision (qwen2.5vl:3b) ──────────────────

async def _extract_via_ollama(b64_image: str) -> list[dict] | None:
    """Local extraction via qwen2.5vl:3b with enforced JSON schema."""
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(f"{_OLLAMA_URL}/api/chat", json={
                "model": _VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": _EXTRACT_PROMPT,
                    "images": [b64_image],
                }],
                "format": _VOCAB_SCHEMA,   # ← enforced structured output
                "stream": False,
                "options": {"temperature": 0.1},
            })
            resp.raise_for_status()

        raw = resp.json().get("message", {}).get("content", "")
        data = json.loads(raw)
        words = data.get("words", []) if isinstance(data, dict) else data
        if isinstance(words, list) and words:
            log.info("Ollama vision extracted %d words", len(words))
            return _normalize(words)
    except Exception as e:
        log.warning("Ollama vision failed: %s", e)
    return None


# ── Strategy 3: Legacy macOS Vision OCR + LLM ──────────────────

async def _extract_via_legacy(image_path: Path) -> list[dict]:
    """Text-based fallback. Only used when both vision strategies fail."""
    tools_dir = Path(__file__).resolve().parent.parent / "tools"
    ocr_bin = tools_dir / "nss_ocr"
    struct_model = os.getenv("OLLAMA_EVAL_MODEL", "gemma2:2b")

    if not ocr_bin.exists():
        log.warning("Legacy OCR binary not found: %s", ocr_bin)
        return []

    jpeg = await _convert_to_jpeg(image_path)
    proc = await asyncio.create_subprocess_exec(
        str(ocr_bin), str(jpeg),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return []

    ocr_text = stdout.decode("utf-8").strip()
    if not ocr_text:
        return []

    prompt = f"""Convert this vocabulary text into a JSON object.
Format: {{"words": [{{"word": "...", "pos": "...", "definition": "...", "example": "..."}}]}}
Skip headers/page numbers. Return ONLY JSON, no markdown.

Text:
{ocr_text}"""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{_OLLAMA_URL}/api/generate", json={
                "model": struct_model,
                "prompt": prompt,
                "format": _VOCAB_SCHEMA,
                "stream": False,
            })
            resp.raise_for_status()
        raw = resp.json().get("response", "")
        data = json.loads(raw)
        words = data.get("words", [])
        return _normalize(words)
    except Exception as e:
        log.warning("Legacy OCR structuring failed: %s", e)
        return []


# ── Normalization ───────────────────────────────────────────────

_POS_MAP = {
    "noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv",
    "conjunction": "conj", "preposition": "prep", "pronoun": "pron",
    "interjection": "interj",
    "n": "n", "v": "v", "adj": "adj", "adv": "adv",
    "conj": "conj", "prep": "prep", "pron": "pron",
}


def _normalize(entries: list[dict]) -> list[dict]:
    """Clean, deduplicate, and validate extracted entries."""
    seen: set[str] = set()
    out: list[dict] = []
    for e in entries:
        w = e.get("word", "").strip().lower()
        w = re.sub(r'^[✓✔☑*/\\0-9.\s]+', '', w).strip()
        if not w or w in seen or (len(w) < 2 and w not in ('a', 'i')):
            continue
        pos = e.get("pos", "").strip().lower().rstrip(".")
        pos = _POS_MAP.get(pos, pos)
        defn = e.get("definition", "").strip()
        ex = e.get("example", "").strip().strip("[]")
        seen.add(w)
        out.append({"word": w, "pos": pos, "definition": defn, "example": ex})
    return out


# ── Public API ──────────────────────────────────────────────────

async def extract_vocab_from_image(image_path: Path) -> list[dict]:
    """Extract vocabulary from a single image file.

    Tries Gemini → Ollama vision → legacy OCR in order.
    Returns a list of {word, pos, definition, example} dicts.
    """
    jpeg = await _convert_to_jpeg(image_path)
    b64 = _image_to_base64(jpeg)

    result = await _extract_via_gemini(b64)
    if result:
        return result

    result = await _extract_via_ollama(b64)
    if result:
        return result

    return await _extract_via_legacy(image_path)


async def extract_vocab_from_bytes(
    image_bytes: bytes,
    filename: str = "upload.jpg",
    prompt: str | None = None,          # kept for backward compat, ignored
) -> list[dict]:
    """Public API: image bytes → list[dict].

    This is the single entry point for all OCR in the app.
    The `prompt` parameter is accepted but ignored (the internal
    _EXTRACT_PROMPT is always used for consistency).
    """
    suffix = Path(filename).suffix.lower() or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp_path.write_bytes(image_bytes)
    try:
        return await extract_vocab_from_image(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


async def extract_text(image_path: Path) -> str:
    """Legacy: macOS Vision OCR raw text extraction.
    Kept for backward compatibility with main.py imports.
    """
    tools_dir = Path(__file__).resolve().parent.parent / "tools"
    ocr_bin = tools_dir / "nss_ocr"
    if not ocr_bin.exists():
        raise FileNotFoundError(f"OCR binary not found: {ocr_bin}")
    jpeg = await _convert_to_jpeg(image_path)
    proc = await asyncio.create_subprocess_exec(
        str(ocr_bin), str(jpeg),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"OCR failed: {stderr.decode()}")
    return stdout.decode("utf-8").strip()


def _regex_parse_vocab(ocr_text: str) -> list[dict]:
    """Legacy regex parser. Kept for backward compatibility."""
    # Minimal implementation — just try to find word(pos) patterns
    results = []
    pattern = re.compile(
        r'^([a-zA-Z][a-zA-Z\s\'-]*?)\s*[\(\[](n|v|adj|adv|conj|prep|pron)\.?[\)\]]',
        re.IGNORECASE | re.MULTILINE
    )
    for m in pattern.finditer(ocr_text):
        w = m.group(1).strip().lower()
        p = m.group(2).strip().lower()
        if w and w not in {e["word"] for e in results}:
            results.append({"word": w, "pos": p, "definition": "", "example": ""})
    return results
