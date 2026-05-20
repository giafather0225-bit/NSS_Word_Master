"""
routers/files_common.py — Shared helpers for the file/voca/OCR routers
Section: English / System
Dependencies: database, utils

Extracted from routers/files.py (2026-05) when that module exceeded the
~500-line limit. Holds the validators, streaming-upload helper, path
constants, and vocab-entry predicate shared by:
  - routers/files.py       (lesson storage routes)
  - routers/files_voca.py  (voca folder + OCR pipeline routes)
"""

import logging
import re as _re
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.database import LEARNING_ROOT
from backend.utils import (
    validate_name as _validate_name_u,
    validate_lesson as _validate_lesson_u,
)

logger = logging.getLogger("backend.routers.files")

# ── Path constants ─────────────────────────────────────────
VOCA_ROOT = LEARNING_ROOT / "English" / "Voca_8000"

_SAFE_FILENAME_RE  = _re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\-. ]{0,99}\.[a-z]{2,5}$')
ALLOWED_UPLOAD_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif", ".bmp", ".pdf"}
MAX_UPLOAD_BYTES   = 20_000_000  # 20 MB
CHUNK_SIZE         = 1_048_576   # 1 MB — streaming chunk size

# ── Magic-byte signatures ──────────────────────────────────
# Maps lower-case extension → list of accepted byte prefixes.
# .heic/.heif use a variable ISO Base Media File Format "ftyp" box whose
# first 12 bytes differ by encoder; we skip the signature check and rely on
# PIL to reject invalid HEIC content instead.
_IMAGE_MAGIC: dict[str, list[bytes]] = {
    ".jpg":  [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png":  [b"\x89PNG\r\n\x1a\n"],
    ".webp": [b"RIFF"],          # first 4 bytes; bytes 8-11 are b"WEBP"
    ".gif":  [b"GIF87a", b"GIF89a"],
    ".bmp":  [b"BM"],
    ".pdf":  [b"%PDF"],
}


def check_upload_magic(raw_head: bytes, ext: str) -> bool:
    """Return True if ``raw_head`` starts with the expected magic bytes for ``ext``.

    Pass at least 12 bytes.  Returns True for extensions without a known
    signature (e.g. .heic/.heif) so callers need no special-casing.
    """
    sigs = _IMAGE_MAGIC.get(ext, [])
    if not sigs:
        return True  # no known signature → defer to downstream processor
    return any(raw_head.startswith(sig) for sig in sigs)


# ── Validators ─────────────────────────────────────────────

def _validate_name(name: str, field: str) -> str:
    """Validate a subject/textbook name (path-traversal safe)."""
    return _validate_name_u(name, field)


def _validate_lesson(lesson: str) -> str:
    """Validate / normalize a lesson key (path-traversal safe)."""
    return _validate_lesson_u(lesson)


def _validate_lang(lang: str) -> str:
    """Validate Tesseract language code to prevent parameter injection."""
    l = lang.strip()
    if not _re.match(r'^[a-zA-Z0-9\+]+$', l):
        raise HTTPException(status_code=400, detail="Invalid lang parameter")
    return l


# ── Streaming upload helper ────────────────────────────────
# Replaces the `raw = await file.read()` pattern that loaded 10–20 MB per
# file into memory. A parent uploading 10 photos used to spike ~200 MB peak
# RSS; this streams in 1 MB chunks and caps peak at ~CHUNK_SIZE regardless
# of file count.

async def _stream_save_upload(
    file: UploadFile,
    dest: Path,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> int:
    """Stream an UploadFile to `dest` in chunks, enforcing max_bytes.

    Returns total bytes written. Raises HTTPException(413) if oversized,
    HTTPException(400) if empty. Cleans up partial file on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="File too large (max 20 MB)")
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        logger.error("Upload save failed for %s: %s", dest.name, e)
        raise HTTPException(status_code=500, detail="File upload failed. Please try again.") from e

    if total == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")
    return total


def _has_def_ex(e: dict) -> bool:
    """Return True if a vocab entry has a definition or example field."""
    for dk in ("definition", "meaning", "question", "desc", "description"):
        if isinstance(e.get(dk), str) and e[dk].strip():
            return True
    for ek in ("example", "example_sentence", "sentence", "sentences"):
        if isinstance(e.get(ek), str) and e[ek].strip():
            return True
    return False
