"""
routers/files_voca.py — Voca-folder CRUD routes (upload, serve, delete, save-reviewed)
Section: English / System
Dependencies: database, models, file_storage, voca_sync, files_common
API:
  POST   /api/voca/save-reviewed
  POST   /api/voca/folder-upload/{lesson}
  GET    /api/voca/folder-image/{lesson}/{filename}
  DELETE /api/voca/folder-image/{lesson}/{filename}

OCR/ingest routes live in routers/files_voca_ocr.py.
Shared helpers live in routers/files_common.py.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db, LEARNING_ROOT
from backend.models import StudyItem
from backend.voca_sync import sync_lesson_to_db
from backend.routers.files_common import (
    logger,  # noqa: F401 — imported for side-effect (shared logging config)
    VOCA_ROOT,
    _SAFE_FILENAME_RE,
    _validate_name,
    _validate_lesson,
    _stream_save_upload,
    check_upload_magic,
)

router = APIRouter()


# @tag FILES @tag OCR @tag VOCA
@router.post("/api/voca/save-reviewed")
def voca_save_reviewed(
    lesson: str = Form(...),
    words_json: str = Form(...),
    textbook: str = Form("Voca_8000"),
    db: Session = Depends(get_db),
):
    """Save user-reviewed/edited words to data.json and sync to DB."""
    try:
        words = json.loads(words_json)
    except ValueError:
        raise HTTPException(422, "Invalid JSON")
    lesson_key = _validate_lesson(lesson)
    textbook   = _validate_name(textbook, "textbook")
    dir_path = LEARNING_ROOT / "English" / textbook / lesson_key
    dir_path.mkdir(parents=True, exist_ok=True)
    out = dir_path / "data.json"

    if not words:
        out.write_text("[]", encoding="utf-8")
        db.query(StudyItem).filter(
            StudyItem.subject == "English",
            StudyItem.textbook == textbook,
            StudyItem.lesson == lesson_key,
        ).delete()
        db.commit()
        return {"lesson": lesson_key, "synced": 0, "data_json": str(out)}

    out.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
    result = sync_lesson_to_db(
        db, LEARNING_ROOT / "English" / textbook, lesson_key, words,
        subject="English", textbook=textbook,
    )
    return {
        "lesson": lesson_key,
        "synced": result["synced"],
        "skipped": result["skipped"],
        "data_json": str(out),
    }


# @tag FILES @tag VOCA @tag FOLDERS
@router.post("/api/voca/folder-upload/{lesson}")
async def voca_folder_upload(
    lesson: str,
    textbook: str = "Voca_8000",
    files: list[UploadFile] = File(...),
):
    """Upload multiple image files into a lesson folder."""
    lesson_key = _validate_lesson(lesson)
    textbook   = _validate_name(textbook, "textbook")
    lesson_dir = LEARNING_ROOT / "English" / textbook / lesson_key
    lesson_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    skipped: list[str] = []
    allowed = (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
    # Stream every file directly to disk — peak RSS per request ≈ CHUNK_SIZE
    # regardless of how many photos are uploaded at once.
    for f in files:
        raw_name = Path(f.filename or "").name
        ext = Path(raw_name).suffix.lower() if raw_name else ".png"
        if ext not in allowed:
            skipped.append(f"{raw_name}: ext")
            continue
        if not raw_name or not _SAFE_FILENAME_RE.match(raw_name):
            skipped.append(f"{raw_name}: invalid name")
            continue

        dest = lesson_dir / raw_name
        counter = 1
        while dest.exists():
            stem = Path(raw_name).stem
            dest = lesson_dir / f"{stem}_{counter}{ext}"
            counter += 1
        try:
            await _stream_save_upload(f, dest)
        except HTTPException as e:
            skipped.append(f"{raw_name}: {e.detail}")
            continue
        # Verify magic bytes match the declared extension.
        with open(dest, "rb") as fh:
            head = fh.read(16)
        if not check_upload_magic(head, ext):
            dest.unlink(missing_ok=True)
            skipped.append(f"{raw_name}: content does not match extension")
            continue
        saved.append(dest.name)
    return {
        "lesson": lesson_key,
        "saved": saved,
        "count": len(saved),
        "skipped": skipped,
    }


# @tag FILES @tag VOCA @tag IMAGES
@router.get("/api/voca/folder-image/{lesson}/{filename}")
def serve_voca_image(lesson: str, filename: str):
    """Serve an image file from a lesson folder."""
    lesson_key = _validate_lesson(lesson)
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    fpath = (VOCA_ROOT / lesson_key / filename).resolve()
    if not str(fpath).startswith(str(VOCA_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    mt_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp",
        ".heic": "image/heic", ".heif": "image/heif",
    }
    mt = mt_map.get(fpath.suffix.lower(), "application/octet-stream")
    return FileResponse(fpath, media_type=mt)


# @tag FILES @tag VOCA @tag IMAGES
@router.delete("/api/voca/folder-image/{lesson}/{filename}")
def delete_voca_image(lesson: str, filename: str, textbook: str = "Voca_8000"):
    """Delete a single image from a lesson folder."""
    lesson_key = _validate_lesson(lesson)
    textbook   = _validate_name(textbook, "textbook")
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    fpath = (LEARNING_ROOT / "English" / textbook / lesson_key / filename).resolve()
    if not str(fpath).startswith(str((LEARNING_ROOT / "English" / textbook).resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    fpath.unlink()
    return {"deleted": True, "filename": filename}
