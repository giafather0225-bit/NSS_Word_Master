"""OCR pipeline — image/PDF → text → Ollama refine → words + study_items save.

Flow:
  1. Image (JPG/PNG): Tesseract → raw text
     PDF (scanned): pymupdf pages → images → Tesseract → raw text
  2. raw text → Ollama gemma2:2b → [{word, definition, example, pos}] JSON
  3. DB save: words table (source records) + study_items table (app study items)

Environment variables:
  TESSERACT_CMD    — tesseract binary path (default: auto-detect)
  OLLAMA_HOST      — Ollama server (default: http://127.0.0.1:11434)
  OLLAMA_OCR_MODEL — refinement model (default: gemma2:2b)
"""
from typing import Optional

import io
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

from backend.models import Word, StudyItem, Lesson
from backend.file_storage import STORAGE_ROOT
from backend.utils import parse_json_array, strip_json_fences

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
OLLAMA_HOST      = os.environ.get("OLLAMA_HOST",      "http://127.0.0.1:11434")
OLLAMA_OCR_MODEL = os.environ.get("OLLAMA_OCR_MODEL", "gemma2:2b")

_TESSERACT_CANDIDATES = [
    os.environ.get("TESSERACT_CMD", ""),
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
]

# Configure pytesseract
try:
    import pytesseract
    _cmd = next((c for c in _TESSERACT_CANDIDATES if c and Path(c).is_file()), None)
    if _cmd:
        pytesseract.pytesseract.tesseract_cmd = _cmd
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

# pymupdf (PDF → images)
try:
    import fitz as _fitz   # type: ignore[import]
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False


# ──────────────────────────────────────────────
# 1. OCR layer
# ──────────────────────────────────────────────

def _image_bytes_to_pil(image_bytes: bytes):
    """bytes → PIL Image."""
    from PIL import Image
    return Image.open(io.BytesIO(image_bytes))


def ocr_image_tesseract(image_bytes: bytes, lang: str = "eng") -> str:
    """Extract text from an image using Tesseract.

    Args:
        image_bytes: JPEG/PNG or other image bytes
        lang: Tesseract language code (default 'eng')
    Returns:
        Raw extracted text
    Raises:
        RuntimeError: Tesseract not installed or OCR error
    """
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract is not installed. Run: pip install pytesseract")

    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    # Convert to grayscale for better OCR accuracy
    if img.mode not in ("L", "1"):
        img = img.convert("L")

    config = "--oem 3 --psm 6"   # single uniform text block mode
    text = pytesseract.image_to_string(img, lang=lang, config=config)
    return text.strip()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Convert each PDF page to a JPEG bytes list using pymupdf.

    Args:
        pdf_bytes: PDF file bytes
        dpi: rendering resolution (200–300 recommended for scanned pages)
    Returns:
        List of JPEG bytes, one per page
    Raises:
        RuntimeError: pymupdf not installed
    """
    if not _PYMUPDF_AVAILABLE:
        raise RuntimeError("pymupdf is not installed. Run: pip install pymupdf")

    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # scale factor relative to 72 dpi base

    pages: list[bytes] = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pages.append(pix.tobytes("jpeg"))

    doc.close()
    return pages


def ocr_pdf_tesseract(pdf_bytes: bytes, lang: str = "eng", max_pages: int = 30) -> str:
    """Run Tesseract OCR on each page of a scanned PDF and join the results.

    Args:
        pdf_bytes: PDF file bytes
        lang: Tesseract language code
        max_pages: maximum pages to process (safety cap)
    Returns:
        Full extracted text with page separators
    """
    images = pdf_to_images(pdf_bytes)[:max_pages]
    parts: list[str] = []
    for i, img_bytes in enumerate(images, 1):
        try:
            text = ocr_image_tesseract(img_bytes, lang=lang)
            if text:
                parts.append(f"--- Page {i} ---\n{text}")
        except Exception as e:
            parts.append(f"--- Page {i} [OCR error: {e}] ---")
    return "\n\n".join(parts)


# ──────────────────────────────────────────────
# 2. Ollama refinement layer
# ──────────────────────────────────────────────


# ──────────────────────────────────────────────
# 3. DB save layer
# ──────────────────────────────────────────────

def save_words_to_db(
    db,
    entries: list[dict],
    lesson_id: int,
    ocr_engine: str = "tesseract",
) -> tuple[int, int]:
    """Save refined vocabulary entries to the words + study_items tables.

    Duplicate words (same lesson_id + word) are overwritten.

    Returns:
        (words_saved, study_items_saved) tuple of saved row counts
    """
    now = datetime.now(timezone.utc).isoformat()

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    subject  = lesson.subject      if lesson else "English"
    textbook = lesson.textbook     if lesson else ""
    lesson_name = lesson.lesson_name if lesson else f"lesson_{lesson_id}"

    words_saved = 0
    items_saved = 0

    for entry in entries:
        w = entry["word"]

        # ── words table ───────────────────────────
        existing_word = (
            db.query(Word)
            .filter(Word.word == w, Word.lesson_id == lesson_id)
            .first()
        )
        if existing_word:
            existing_word.definition = entry["definition"]
            existing_word.example    = entry["example"]
            existing_word.pos        = entry["pos"]
            existing_word.ocr_engine = ocr_engine
            word_obj = existing_word
        else:
            word_obj = Word(
                word=w,
                definition=entry["definition"],
                example=entry["example"],
                pos=entry["pos"],
                lesson_id=lesson_id,
                source_type="ocr",
                ocr_engine=ocr_engine,
                created_at=now,
            )
            db.add(word_obj)
        words_saved += 1

        # ── study_items table ─────────────────────
        existing_item = (
            db.query(StudyItem)
            .filter(
                StudyItem.answer == w,
                StudyItem.lesson_id == lesson_id,
            )
            .first()
        )
        extra = json.dumps({"pos": entry["pos"]}, ensure_ascii=False)
        if existing_item:
            existing_item.question    = entry["definition"]
            existing_item.hint        = entry["example"]
            existing_item.extra_data  = extra
            existing_item.source_type = "ocr"
        else:
            db.add(StudyItem(
                subject=subject,
                textbook=textbook,
                lesson=lesson_name,
                lesson_id=lesson_id,
                source_type="ocr",
                question=entry["definition"],
                answer=w,
                hint=entry["example"],
                extra_data=extra,
            ))
        items_saved += 1

    db.commit()

    # Link word_obj → study_item_id (post-processing)
    _link_word_study_items(db, lesson_id)

    return words_saved, items_saved


def _link_word_study_items(db, lesson_id: int) -> None:
    """Backfill words.study_item_id ← study_items.id back-reference."""
    words = db.query(Word).filter(Word.lesson_id == lesson_id, Word.study_item_id == None).all()
    for word_obj in words:
        item = (
            db.query(StudyItem)
            .filter(
                StudyItem.answer == word_obj.word,
                StudyItem.lesson_id == lesson_id,
            )
            .first()
        )
        if item:
            word_obj.study_item_id = item.id
    db.commit()


# ──────────────────────────────────────────────
# 4. Full pipeline entry point
# ──────────────────────────────────────────────

async def run_ocr_pipeline(
    lesson_id: int,
    db,
    lang: str = "eng",
    model: Optional[str] = None,
) -> dict:
    """Main pipeline: run OCR on stored files and save results to DB.

    Processes image/PDF files in storage/lessons/{lesson_id}/ in order.

    Returns:
        {
          "lesson_id": int,
          "files_processed": int,
          "words_saved": int,
          "study_items_saved": int,
          "errors": [str],
        }
    """
    lesson_dir = STORAGE_ROOT / str(lesson_id)
    if not lesson_dir.exists():
        raise FileNotFoundError(f"storage/lessons/{lesson_id}/ does not exist")

    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    PDF_EXTS   = {".pdf"}

    target_files = sorted(
        p for p in lesson_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTS | PDF_EXTS
        and not p.name.startswith("_")  # exclude _index.json
    )

    if not target_files:
        raise FileNotFoundError(f"No image/PDF files to process (lesson_id={lesson_id})")

    all_entries: list[dict] = []
    errors: list[str] = []
    files_processed = 0

    for fpath in target_files:
        raw = fpath.read_bytes()
        ext = fpath.suffix.lower()

        try:
            # ── OCR ─────────────────────────────────
            if ext in PDF_EXTS:
                ocr_text = ocr_pdf_tesseract(raw, lang=lang)
                engine = "tesseract+pymupdf"
            else:
                ocr_text = ocr_image_tesseract(raw, lang=lang)
                engine = "tesseract"

            if not ocr_text.strip():
                errors.append(f"{fpath.name}: OCR produced no text (empty result)")
                continue

            # ── Hybrid AI refinement (Ollama → Gemini fallback) ──
            from backend.ai_service import smart_refine
            result  = await smart_refine(ocr_text)
            entries = result["entries"]
            for e in entries:
                e["_engine"]   = engine
                e["_provider"] = "+".join(result["providers"])
            all_entries.extend(entries)
            files_processed += 1

        except Exception as e:
            errors.append(f"{fpath.name}: {e!s}")

    if not all_entries:
        return {
            "lesson_id":       lesson_id,
            "files_processed": files_processed,
            "words_saved":     0,
            "study_items_saved": 0,
            "errors":          errors,
        }

    # Deduplicate by lowercase word — last entry wins
    seen: dict[str, dict] = {}
    for e in all_entries:
        seen[e["word"].lower()] = e

    unique = list(seen.values())
    engine_label   = unique[0].get("_engine",   "tesseract") if unique else "tesseract"
    provider_label = unique[0].get("_provider", "ollama")    if unique else "ollama"
    for e in unique:
        e.pop("_engine",   None)
        e.pop("_provider", None)

    ocr_engine_tag = f"{engine_label}+{provider_label}"
    words_saved, items_saved = save_words_to_db(db, unique, lesson_id, ocr_engine=ocr_engine_tag)

    return {
        "lesson_id":         lesson_id,
        "files_processed":   files_processed,
        "words_saved":       words_saved,
        "study_items_saved": items_saved,
        "errors":            errors,
    }
