"""OCR 파이프라인 — 이미지/PDF → 텍스트 → Ollama 정제 → words + study_items 저장.

흐름:
  1. 이미지(JPG/PNG): Tesseract → raw text
     PDF(스캔): pymupdf 페이지 → 이미지 → Tesseract → raw text
  2. raw text → Ollama gemma2:2b → [{word, definition, example, pos}] JSON
  3. DB 저장: words 테이블(원본 레코드) + study_items 테이블(앱 학습용)

환경 변수:
  TESSERACT_CMD  — tesseract 바이너리 경로 (기본: 자동 탐지)
  OLLAMA_HOST    — Ollama 서버 (기본: http://127.0.0.1:11434)
  OLLAMA_OCR_MODEL — 정제용 모델 (기본: gemma2:2b)
"""
from __future__ import annotations

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
# 설정
# ──────────────────────────────────────────────
OLLAMA_HOST      = os.environ.get("OLLAMA_HOST",      "http://127.0.0.1:11434")
OLLAMA_OCR_MODEL = os.environ.get("OLLAMA_OCR_MODEL", "gemma2:2b")

_TESSERACT_CANDIDATES = [
    os.environ.get("TESSERACT_CMD", ""),
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
]

# pytesseract 설정
try:
    import pytesseract
    _cmd = next((c for c in _TESSERACT_CANDIDATES if c and Path(c).is_file()), None)
    if _cmd:
        pytesseract.pytesseract.tesseract_cmd = _cmd
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

# pymupdf (PDF → 이미지)
try:
    import fitz as _fitz   # type: ignore[import]
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False


# ──────────────────────────────────────────────
# 1. OCR 레이어
# ──────────────────────────────────────────────

def _image_bytes_to_pil(image_bytes: bytes):
    """bytes → PIL Image."""
    from PIL import Image
    return Image.open(io.BytesIO(image_bytes))


def ocr_image_tesseract(image_bytes: bytes, lang: str = "eng") -> str:
    """Tesseract로 이미지에서 텍스트 추출.

    Args:
        image_bytes: JPEG/PNG 등 이미지 바이트
        lang: Tesseract 언어 코드 (기본 'eng')
    Returns:
        추출된 원시 텍스트
    Raises:
        RuntimeError: Tesseract 미설치 또는 오류
    """
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract 미설치. pip install pytesseract")

    import pytesseract
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    # 그레이스케일 변환 → OCR 정확도 향상
    if img.mode not in ("L", "1"):
        img = img.convert("L")

    config = "--oem 3 --psm 6"   # 단일 블록 텍스트 모드
    text = pytesseract.image_to_string(img, lang=lang, config=config)
    return text.strip()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """PDF 각 페이지를 JPEG bytes 목록으로 변환 (pymupdf 사용).

    Args:
        pdf_bytes: PDF 파일 바이트
        dpi: 렌더링 해상도 (스캔본 권장: 200~300)
    Returns:
        페이지별 JPEG bytes 리스트
    Raises:
        RuntimeError: pymupdf 미설치
    """
    if not _PYMUPDF_AVAILABLE:
        raise RuntimeError("pymupdf 미설치. pip install pymupdf")

    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72dpi 기준 배율

    pages: list[bytes] = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pages.append(pix.tobytes("jpeg"))

    doc.close()
    return pages


def ocr_pdf_tesseract(pdf_bytes: bytes, lang: str = "eng", max_pages: int = 30) -> str:
    """PDF 스캔본 → 페이지별 Tesseract OCR → 전체 텍스트 결합.

    Args:
        pdf_bytes: PDF 파일 바이트
        lang: Tesseract 언어 코드
        max_pages: 처리할 최대 페이지 수 (안전 제한)
    Returns:
        전체 추출 텍스트 (페이지 구분선 포함)
    """
    images = pdf_to_images(pdf_bytes)[:max_pages]
    parts: list[str] = []
    for i, img_bytes in enumerate(images, 1):
        try:
            text = ocr_image_tesseract(img_bytes, lang=lang)
            if text:
                parts.append(f"--- Page {i} ---\n{text}")
        except Exception as e:
            parts.append(f"--- Page {i} [OCR 오류: {e}] ---")
    return "\n\n".join(parts)


# ──────────────────────────────────────────────
# 2. Ollama 정제 레이어
# ──────────────────────────────────────────────


# ──────────────────────────────────────────────
# 3. DB 저장 레이어
# ──────────────────────────────────────────────

def save_words_to_db(
    db,
    entries: list[dict],
    lesson_id: int,
    ocr_engine: str = "tesseract",
) -> tuple[int, int]:
    """정제된 단어 목록을 words + study_items 테이블에 저장.

    중복 단어(같은 lesson_id + word)는 덮어씁니다.

    Returns:
        (words_saved, study_items_saved) 저장 건수 튜플
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

        # ── words 테이블 ──────────────────────────
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

        # ── study_items 테이블 ────────────────────
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

    # word_obj → study_item_id 연결 (후처리)
    _link_word_study_items(db, lesson_id)

    return words_saved, items_saved


def _link_word_study_items(db, lesson_id: int) -> None:
    """words.study_item_id ← study_items.id 역참조 채우기."""
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
# 4. 전체 파이프라인 진입점
# ──────────────────────────────────────────────

async def run_ocr_pipeline(
    lesson_id: int,
    db,
    lang: str = "eng",
    model: str | None = None,
) -> dict:
    """저장된 파일들에 OCR을 실행하고 DB에 저장하는 메인 파이프라인.

    storage/lessons/{lesson_id}/ 의 이미지/PDF 파일을 순서대로 처리.

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
        raise FileNotFoundError(f"storage/lessons/{lesson_id}/ 없음")

    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    PDF_EXTS   = {".pdf"}

    target_files = sorted(
        p for p in lesson_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTS | PDF_EXTS
        and not p.name.startswith("_")  # _index.json 제외
    )

    if not target_files:
        raise FileNotFoundError(f"처리할 이미지/PDF 파일 없음 (lesson_id={lesson_id})")

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
                errors.append(f"{fpath.name}: OCR 결과 없음 (빈 텍스트)")
                continue

            # ── 하이브리드 AI 정제 (Ollama → Gemini 폴백) ──
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

    # 중복 단어 제거 (word 소문자 기준, 마지막 항목 우선)
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
