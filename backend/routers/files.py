"""
routers/files.py — Lesson file upload, storage, and OCR-trigger routes
Section: English / System
Dependencies: database, models, file_storage, ocr_pipeline, ocr_vision, ai_tutor,
              voca_sync, files_common
API:
  POST   /api/files/upload
  POST   /api/storage/lessons/{lesson_id}/files
  GET    /api/storage/lessons/{lesson_id}/files
  DELETE /api/storage/lessons/{lesson_id}/files/{filename}
  POST   /api/storage/lessons/{lesson_id}/ocr

Voca-folder ingestion + OCR-pipeline routes (/api/voca/*, /api/ocr/*,
/api/lessons/ingest_disk) were split into routers/files_voca.py (2026-05)
when this module exceeded the ~500-line limit. Shared helpers live in
routers/files_common.py.
"""
from typing import Optional

import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from backend.utils import ocr_limiter
from sqlalchemy.orm import Session

from backend.database import get_db, LEARNING_ROOT
from backend.models import Lesson
from backend.file_storage import save_lesson_file, list_lesson_files, delete_lesson_file
from backend.ocr_pipeline import run_ocr_pipeline
from backend.ocr_vision import extract_vocab_from_bytes
from backend.ai_tutor import ollama_enrich_vocab
from backend.voca_sync import sync_lesson_to_db
from backend.routers.files_common import (
    logger,
    ALLOWED_UPLOAD_EXTS,
    _validate_name,
    _validate_lesson,
    _validate_lang,
    _stream_save_upload,
    _has_def_ex,
    check_upload_magic,
)

router = APIRouter()


# ── Routes ─────────────────────────────────────────────────

# @tag FILES @tag UPLOAD
@router.post("/api/files/upload")
async def files_upload(
    subject:  str = Form(...),
    textbook: str = Form(...),
    lesson:   str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image → OCR → save data.json → sync DB.

    Accepts multipart/form-data with {subject, textbook, lesson, file}.
    """
    subject_key  = _validate_name(subject, "subject")
    textbook_key = _validate_name(textbook, "textbook")
    lesson_key   = _validate_lesson(lesson)

    fname = file.filename or "upload.png"
    ext = Path(fname).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    dir_path = LEARNING_ROOT / subject_key / textbook_key / lesson_key
    src_path = dir_path / f"source{ext}"
    await _stream_save_upload(file, src_path)
    raw = src_path.read_bytes()  # single read for OCR — peak = 1× file size

    # Verify file content matches the declared extension before sending to OCR.
    if not check_upload_magic(raw[:16], ext):
        src_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match extension '{ext}'. Please upload a valid image or PDF.",
        )

    try:
        data = await extract_vocab_from_bytes(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vision OCR error: {e!s}")
    finally:
        del raw  # release ASAP

    if not data:
        raise HTTPException(status_code=422, detail="OCR extracted no vocabulary words.")

    if not any(_has_def_ex(e) for e in data):
        try:
            data = await ollama_enrich_vocab(data)
        except Exception as _enrich_err:
            logger.warning("ollama_enrich_vocab failed: %s", _enrich_err)
            raise HTTPException(
                status_code=422,
                detail="AI definition generation failed. Please retry — we won't save incomplete word data.",
            )

    (dir_path / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    result = sync_lesson_to_db(
        db,
        LEARNING_ROOT / subject_key / textbook_key,
        lesson_key,
        data,
        subject=subject_key,
        textbook=textbook_key,
    )
    if result["synced"] == 0:
        raise HTTPException(
            status_code=422,
            detail=f"No valid words to save. Skipped {result['skipped']} rows: {'; '.join(result['reasons'][:3])}",
        )
    return {
        "subject": subject_key,
        "textbook": textbook_key,
        "lesson": lesson_key,
        "synced": result["synced"],
        "skipped": result["skipped"],
        "data_json": str(dir_path / "data.json"),
    }


# @tag FILES @tag STORAGE
@router.post("/api/storage/lessons/{lesson_id}/files")
async def upload_lesson_file(
    lesson_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Store a HEIC/PDF/image file under storage/lessons/{lesson_id}/.

    HEIC files are auto-converted to JPG; PDFs are stored as-is.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    original_name = file.filename or "upload.bin"
    # Stream to a temp file first, then hand off bytes to save_lesson_file.
    # Peak RSS = 1× file (unavoidable if save_lesson_file consumes bytes), but
    # parallel uploads no longer share a 10-file spike.
    with tempfile.NamedTemporaryFile(delete=False) as _tmp:
        tmp_path = Path(_tmp.name)
    try:
        await _stream_save_upload(file, tmp_path)
        raw = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    try:
        record = save_lesson_file(lesson_id, raw, original_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "lesson_id":     lesson_id,
        "lesson_name":   lesson.lesson_name,
        "filename":      record["filename"],
        "original_name": record["original_name"],
        "content_type":  record["content_type"],
        "size":          record["size"],
        "converted":     record["converted"],
        "pages":         record["pages"],
        "path":          record["path"],
    }


# @tag FILES @tag STORAGE
@router.get("/api/storage/lessons/{lesson_id}/files")
def list_uploaded_files(lesson_id: int, db: Session = Depends(get_db)):
    """Return the list of files uploaded for lesson_id."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    files = list_lesson_files(lesson_id)
    return {
        "lesson_id":   lesson_id,
        "lesson_name": lesson.lesson_name,
        "files":       files,
        "count":       len(files),
    }


# @tag FILES @tag STORAGE
@router.delete("/api/storage/lessons/{lesson_id}/files/{filename}")
def remove_lesson_file(lesson_id: int, filename: str, db: Session = Depends(get_db)):
    """Delete an uploaded file from storage for lesson_id."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    try:
        deleted = delete_lesson_file(lesson_id, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail=f"파일 '{filename}' 없음")

    return {"deleted": True, "filename": filename, "lesson_id": lesson_id}


# @tag FILES @tag OCR
@router.post("/api/storage/lessons/{lesson_id}/ocr")
async def trigger_ocr(
    lesson_id: int,
    lang: str = "eng",
    model: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(ocr_limiter),
):
    """Run Tesseract OCR + Ollama refinement on stored files and save to words/study_items.

    Query params:
        lang  — Tesseract language code (default 'eng')
        model — Ollama model name (default from OLLAMA_OCR_MODEL env var)
    """
    safe_lang = _validate_lang(lang)

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    try:
        result = await run_ocr_pipeline(lesson_id=lesson_id, db=db, lang=safe_lang, model=model)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR 파이프라인 오류: {e!s}")

    return result
