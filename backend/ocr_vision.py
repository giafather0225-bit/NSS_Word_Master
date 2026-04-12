"""
NSS Word Master — macOS Vision OCR + Ollama structuring pipeline.
Replaces llava-based vision_extract_vocab for M1 8GB compatibility.

Pipeline:
  1. HEIC/image → JPEG (sips)
  2. JPEG → raw text (macOS Vision via compiled Swift binary)
  3. raw text → structured JSON (gemma2:2b via Ollama)
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
_OCR_BIN = _TOOLS_DIR / "nss_ocr"
_OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_STRUCT_MODEL = os.getenv("OLLAMA_EVAL_MODEL", "gemma2:2b")

HEIC_EXTENSIONS = {".heic", ".heif"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"} | HEIC_EXTENSIONS

_STRUCTURING_PROMPT = """Convert this vocabulary text into a JSON array.
Each entry must have exactly these fields:
- "word": the English word (clean, lowercase, no special characters like V or *)
- "pos": part of speech (noun, verb, adjective, adverb, conjunction, preposition)
- "definition": the meaning
- "example": the example sentence (without brackets)

Skip any lines that are headers, page numbers, copyright notices, or review exercises.
Return ONLY the JSON array, nothing else.

Text:
{ocr_text}"""


async def convert_to_jpeg(image_path: Path) -> Path:
    """Convert HEIC or other formats to JPEG using macOS sips into temp dir."""
    if image_path.suffix.lower() in (".jpg", ".jpeg"):
        return image_path

    # Use temp directory to avoid polluting the source folder
    import tempfile
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
async def extract_text(image_path: Path) -> str:
    """Run macOS Vision OCR on an image file. Returns raw text."""
    jpeg = await convert_to_jpeg(image_path)
    
    if not _OCR_BIN.exists():
        raise FileNotFoundError(f"OCR binary not found: {_OCR_BIN}")
    
    proc = await asyncio.create_subprocess_exec(
        str(_OCR_BIN), str(jpeg),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"OCR failed: {stderr.decode()}")
    
    text = stdout.decode("utf-8").strip()
    log.info("OCR extracted %d chars from %s", len(text), image_path.name)
    return text


async def structure_vocab(ocr_text: str) -> list[dict]:
    """Send raw OCR text to gemma2:2b to get structured JSON."""
    prompt = _STRUCTURING_PROMPT.format(ocr_text=ocr_text)
    
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{_OLLAMA_URL}/api/generate", json={
            "model": _STRUCT_MODEL,
            "prompt": prompt,
            "stream": False,
        })
        resp.raise_for_status()
    
    raw = resp.json().get("response", "")
    
    # Strip markdown fences
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())
    
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        log.warning("Could not find JSON array in LLM response")
        return []
    
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        log.warning("JSON parse error: %s", e)
        return []
    
    # Normalize fields
    cleaned = []
    for entry in data:
        word = entry.get("word", "").strip().lower()
        if not word:
            continue
        cleaned.append({
            "word": word,
            "pos": entry.get("pos", "").strip().lower(),
            "definition": entry.get("definition", "").strip(),
            "example": entry.get("example", "").strip().strip("[]"),
        })
    
    log.info("Structured %d vocabulary entries", len(cleaned))
    return cleaned


async def extract_vocab_from_bytes(image_bytes: bytes, filename: str = "upload.jpg") -> list[dict]:
    """Public API: image bytes → structured vocab list via Vision OCR + Ollama.

    Used by /api/voca/ocr-preview and /api/voca/ingest endpoints.
    """
    suffix = Path(filename).suffix.lower() or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp_path.write_bytes(image_bytes)

    jpeg_path: Path | None = None
    try:
        jpeg_path = await convert_to_jpeg(tmp_path)
        ocr_text = await extract_text(jpeg_path)
        return await structure_vocab(ocr_text)
    finally:
        tmp_path.unlink(missing_ok=True)
        if jpeg_path is not None and jpeg_path != tmp_path:
            jpeg_path.unlink(missing_ok=True)






def _regex_parse_vocab(ocr_text: str) -> list[dict]:
    """Parse Voca 8000 format. Handles stacked words and OCR artifacts."""
    import re as _re

    text = ocr_text.strip()
    text = _re.sub(r"[\u00a9\u00ae].*$", "", text, flags=_re.MULTILINE)

    lines = text.split("\n")
    clean = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _re.match(r"^(Voca\s*8000|Words\s+in\s+English|Lesson\s+\d+|\d+)$", s, _re.IGNORECASE):
            continue
        clean.append(s)

    processed = []
    for line in clean:
        line = _re.sub(r"^[Nn][^\x00-\x7f](?=[a-z])", "e", line)
        line = _re.sub(r"^[Vv\\\u2713\u2714\u2611/\\\\]\s*(?=[a-zA-Z])", "", line)
        if _re.match(r"^v[a-z]+\s*[\(\[]", line):
            line = line[1:]
        # Skip short garbage lines like "Wr", "8", single chars
        if len(line) <= 2 and not _re.match(r"^[a-zA-Z]+\s*[\(\[]", line):
            continue
        processed.append(line)

    WORD_RE = _re.compile(
        r"^([a-zA-Z][a-zA-Z\s'-]*?)\s*"
        r"[\(\[]"
        r"(n|v|ad|adj|adv|conj|prep|pron|interj|det)"
        r"\.?"
        r"[\)\]]?"
        r"[\)\]]?"     # handle double )) like (ad))
        r"[\s*\u2605\u2606]*$",
        _re.IGNORECASE
    )

    # Tag each line: 'W' = word line, 'C' = content line
    tagged = []
    for idx, line in enumerate(processed):
        m = WORD_RE.match(line)
        if m:
            tagged.append(('W', idx, m.group(1).strip().lower(), m.group(2).strip().lower()))
        else:
            tagged.append(('C', idx, line, None))

    # Group: find runs of consecutive word lines, then content lines
    # Strategy: collect word headers, then match them with definition blocks
    
    # Split into segments: each segment starts with one or more W lines
    # followed by C lines (definitions + examples)
    segments = []  # list of (word_list, content_lines)
    current_words = []
    current_content = []
    
    for tag, idx, val, pos in tagged:
        if tag == 'W':
            if current_content and current_words:
                # We had words + content, save segment
                segments.append((current_words[:], current_content[:]))
                current_words = []
                current_content = []
            current_words.append((val, pos))  # val=word, pos=pos
        else:  # 'C'
            current_content.append(val)  # val=line text
    
    if current_words:
        segments.append((current_words[:], current_content[:]))

    # Now parse each segment
    entries = []
    for word_list, content_lines in segments:
        if len(word_list) == 1:
            # Simple case: one word, all content belongs to it
            definition, example = _split_def_ex(content_lines, _re)
            entries.append({
                "word": word_list[0][0],
                "pos": word_list[0][1],
                "definition": definition,
                "example": example,
            })
        else:
            # Stacked words: N words listed, then N definition+example blocks
            blocks = _split_into_blocks(content_lines, len(word_list), _re)
            for i, (word, pos) in enumerate(word_list):
                if i < len(blocks):
                    definition, example = blocks[i]
                else:
                    definition, example = "", ""
                entries.append({
                    "word": word,
                    "pos": pos,
                    "definition": definition,
                    "example": example,
                })

    # Deduplicate
    seen = set()
    final = []
    for e in entries:
        if e["word"] and e["word"] not in seen:
            seen.add(e["word"])
            final.append(e)

    log.info("Regex parsed %d words from OCR text", len(final))
    return final


def _split_def_ex(content_lines, _re):
    """Split content lines into (definition, example)."""
    def_parts = []
    ex_parts = []
    in_ex = False
    for line in content_lines:
        # Example starts with [ or (
        if not in_ex and _re.match(r"^[\[\(](?=[A-Z])", line):
            in_ex = True
            ex_text = _re.sub(r"^[\[\(]\s*", "", line)
            if _re.search(r"[\]\)]\.?\s*$", ex_text):
                ex_text = _re.sub(r"[\]\)]+\.?\s*$", "", ex_text)
                ex_parts.append(ex_text.strip())
                in_ex = False
            else:
                ex_parts.append(ex_text.strip())
            continue
        # Bare example: no [ but ends with ] and starts with uppercase
        if not in_ex and _re.match(r"^[A-Z]", line) and _re.search(r"[\]\)]\.?\s*$", line) and def_parts:
            ex_text = _re.sub(r"[\]\)]+\.?\s*$", "", line)
            ex_parts.append(ex_text.strip())
            continue
        if in_ex:
            ex_text = line
            if _re.search(r"[\]\)]\.?\s*$", ex_text):
                ex_text = _re.sub(r"[\]\)]+\.?\s*$", "", ex_text)
                ex_parts.append(ex_text.strip())
                in_ex = False
            else:
                ex_parts.append(ex_text.strip())
            continue
        def_parts.append(line)
    return " ".join(def_parts).strip(), " ".join(ex_parts).strip()


def _split_into_blocks(content_lines, num_words, _re):
    """Split interleaved definition+example blocks for stacked words."""
    blocks = []
    current_def = []
    current_ex = []
    in_ex = False

    def save_block():
        nonlocal current_def, current_ex
        if current_def or current_ex:
            blocks.append((" ".join(current_def).strip(), " ".join(current_ex).strip()))
            current_def = []
            current_ex = []

    def is_ex_start(line):
        return bool(_re.match(r"^[\[\(](?=[A-Z])", line))

    def is_ex_end(line):
        return bool(_re.search(r"[\]\)]\]?\.?\s*$", line))

    def strip_ex_start(line):
        return _re.sub(r"^[\[\(]\s*", "", line)

    def strip_ex_end(line):
        return _re.sub(r"[\]\)]+\.?\s*$", "", line)

    for line in content_lines:
        # Example start with bracket
        if not in_ex and is_ex_start(line):
            in_ex = True
            ex_text = strip_ex_start(line)
            if is_ex_end(ex_text):
                ex_text = strip_ex_end(ex_text)
                current_ex.append(ex_text.strip())
                in_ex = False
            else:
                current_ex.append(ex_text.strip())
            continue

        # Bare example: no [ but ends with ] (OCR missed opening bracket)
        if not in_ex and not is_ex_start(line) and is_ex_end(line) and current_def and _re.match(r"^[A-Z]", line):
            ex_text = strip_ex_end(line)
            current_ex.append(ex_text.strip())
            continue

        if in_ex:
            if is_ex_end(line):
                ex_text = strip_ex_end(line)
                current_ex.append(ex_text.strip())
                in_ex = False
            else:
                if _re.match(r"^[a-z]", line) and "[" not in line and "]" not in line:
                    in_ex = False
                    save_block()
                    current_def.append(line)
                else:
                    current_ex.append(line.strip())
            continue

        # Not in example - this is a definition line
        if current_ex and not in_ex:
            save_block()
        current_def.append(line)

    save_block()

    # Merge numbered sub-definitions (2., 3., ...) into previous block
    # But keep 1. as its own block start
    merged = []
    for d, e in blocks:
        if _re.match(r"^[2-9]\.\s", d) and merged:
            prev_d, prev_e = merged[-1]
            new_d = prev_d + " " + d
            new_e = (prev_e + " " + e).strip() if e else prev_e
            merged[-1] = (new_d, new_e)
        else:
            merged.append((d, e))

    return merged


