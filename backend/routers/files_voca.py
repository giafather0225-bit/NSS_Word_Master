"""
routers/files_voca.py — Voca-folder ingestion + OCR pipeline routes
Section: English / System
Dependencies: database, models, file_storage, ocr_vision, ai_tutor, voca_sync, files_common
API:
  POST   /api/voca/ocr-preview
  POST   /api/voca/save-reviewed
  POST   /api/voca/ingest
  POST   /api/voca/folder-upload/{lesson}
  POST   /api/voca/folder-ocr/{lesson}
  POST   /api/ocr/vocab_image
  POST   /api/lessons/ingest_disk/{lesson}
  GET    /api/voca/folder-image/{lesson}/{filename}
  DELETE /api/voca/folder-image/{lesson}/{filename}

Extracted from routers/files.py (2026-05) when that module exceeded the
~500-line limit. Shared helpers live in routers/files_common.py.
"""

import json
import re as _re
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db, LEARNING_ROOT
from backend.models import StudyItem
from backend.ocr_vision import extract_vocab_from_bytes, extract_vocab_from_image
from backend.ai_tutor import ollama_enrich_vocab
from backend.voca_sync import sync_lesson_to_db
from backend.routers.files_common import (
    logger,
    VOCA_ROOT,
    _SAFE_FILENAME_RE,
    ALLOWED_UPLOAD_EXTS,
    MAX_UPLOAD_BYTES,
    _validate_name,
    _validate_lesson,
    _stream_save_upload,
    _has_def_ex,
)

router = APIRouter()


# @tag FILES @tag OCR @tag VOCA
@router.post("/api/voca/ocr-preview")
async def voca_ocr_preview(files: list[UploadFile] = File(...)):
    """Run OCR on multiple images and return merged+deduped words WITHOUT saving."""
    all_words = []
    seen = set()
    for f in files:
        f_ext = Path(f.filename or "").suffix.lower()
        if f_ext not in ALLOWED_UPLOAD_EXTS:
            continue
        # Pre-check Content-Length before reading to avoid large in-memory reads
        if f.size and f.size > MAX_UPLOAD_BYTES:
            continue
        raw = await f.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            continue
        try:
            words = await extract_vocab_from_bytes(raw, f.filename or "upload.jpg")
            for w in words:
                key = w.get("word", "").strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    all_words.append(w)
        except Exception:
            continue
    if not all_words:
        raise HTTPException(422, "OCR extracted no vocabulary words from any image.")
    return {"words": all_words, "count": len(all_words), "images_processed": len(files)}


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
    except Exception:
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


# @tag FILES @tag OCR @tag VOCA
@router.post("/api/voca/ingest")
async def voca_ingest(
    lesson: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Drop a photo → create Voca_8000/Lesson_XX/data.json + sync DB."""
    lesson_key = _validate_lesson(lesson)

    fname = file.filename or "upload.png"
    ext = Path(fname).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    dir_path = VOCA_ROOT / lesson_key
    src_path = dir_path / f"source{ext}"
    await _stream_save_upload(file, src_path)
    raw = src_path.read_bytes()

    try:
        data = await extract_vocab_from_bytes(raw, fname)
        if not data:
            raise HTTPException(status_code=422, detail="OCR extracted no vocabulary words.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vision OCR error: {e!s}")
    finally:
        del raw

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
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    result = sync_lesson_to_db(db, VOCA_ROOT, lesson_key, data, subject="English", textbook="Voca_8000")
    if result["synced"] == 0:
        raise HTTPException(
            status_code=422,
            detail=f"No valid words to save. Skipped {result['skipped']} rows: {'; '.join(result['reasons'][:3])}",
        )
    return {
        "lesson": lesson_key,
        "synced": result["synced"],
        "skipped": result["skipped"],
        "data_json": str(dir_path / "data.json"),
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
    # Stream every file directly to disk. Peak RSS per request ≈ CHUNK_SIZE,
    # regardless of whether the parent uploads 1 or 50 HEIC photos.
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
            # Per-file skip; don't fail the whole batch.
            skipped.append(f"{raw_name}: {e.detail}")
            continue
        saved.append(dest.name)
    return {
        "lesson": lesson_key,
        "saved": saved,
        "count": len(saved),
        "skipped": skipped,
    }


# @tag FILES @tag OCR @tag VOCA @tag FOLDERS
@router.post("/api/voca/folder-ocr/{lesson}")
async def voca_folder_ocr(
    lesson: str,
    textbook: str = "Voca_8000",
    db: Session = Depends(get_db),
):
    """Run vision-LLM OCR on all images in a lesson folder and save words.

    Uses extract_vocab_from_image() which sends each image directly to a
    vision model (Gemini or qwen2.5vl:3b), preventing definition-shift bugs.
    """
    lesson_key = _validate_lesson(lesson)
    textbook   = _validate_name(textbook, "textbook")
    lesson_dir = LEARNING_ROOT / "English" / textbook / lesson_key
    if not lesson_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {lesson_key}")

    images = sorted(
        f for f in lesson_dir.iterdir()
        if f.suffix.lower() in (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
        and not f.name.startswith(".")
    )
    if not images:
        raise HTTPException(status_code=400, detail="No images in folder")

    all_words: dict[str, dict] = {}
    errors: list[str] = []

    for img_path in images:
        try:
            words = await extract_vocab_from_image(img_path)
            for w in words:
                key = w.get("word", "").strip().lower()
                if not key:
                    continue
                defn = w.get("definition", "")
                w["definition"] = _re.sub(r"(too few samples\s*)+", "", defn).strip()
                if key not in all_words:
                    all_words[key] = w
            logger.info("%s: extracted %d words", img_path.name, len(words))
        except Exception as e:
            errors.append(f"{img_path.name}: {e!s}")
            logger.warning("OCR failed for %s: %s", img_path.name, e)

    words_list = list(all_words.values())
    if not words_list:
        raise HTTPException(status_code=422, detail="OCR extracted no words")

    if not any(w.get("definition") and len(w["definition"]) >= 5 for w in words_list):
        try:
            words_list = await ollama_enrich_vocab(words_list)
        except Exception as enrich_err:
            logger.warning("Enrichment failed: %s", enrich_err)
            raise HTTPException(
                status_code=422,
                detail="AI definition generation failed. Please retry — we won't save incomplete word data.",
            )

    data_json = lesson_dir / "data.json"
    data_json.write_text(
        json.dumps(words_list, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    result = sync_lesson_to_db(db, VOCA_ROOT, lesson_key, words_list, subject="English", textbook=textbook)
    if result["synced"] == 0:
        raise HTTPException(
            status_code=422,
            detail=f"No valid words to save. Skipped {result['skipped']} rows: {'; '.join(result['reasons'][:3])}",
        )

    bad_count = sum(1 for w in words_list if not w.get("definition") or len(w.get("definition", "")) < 5)
    return {
        "lesson": lesson_key,
        "words": words_list,
        "word_count": len(words_list),
        "synced": result["synced"],
        "skipped": result["skipped"],
        "images_processed": len(images),
        "errors": errors,
        "quality": {
            "remaining_issues": bad_count,
            "status": "perfect" if bad_count == 0 else f"{bad_count} words need review",
        },
    }


# @tag FILES @tag OCR
@router.post("/api/ocr/vocab_image")
async def ocr_vocab_image(file: UploadFile = File(...)):
    """Run vision OCR on a single uploaded image and return parsed words."""
    fname = file.filename or "upload.png"
    ext = Path(fname).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    # Preview endpoint — stream to a temp file, then OCR. Temp file is deleted.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as _tmp:
        tmp_path = Path(_tmp.name)
    try:
        await _stream_save_upload(file, tmp_path)
        raw = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    try:
        data = await extract_vocab_from_bytes(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Vision OCR error: {e!s}")
    finally:
        del raw

    if not data:
        return {"parsed": None, "warning": "OCR extracted no vocabulary words."}

    enrich_warning = None
    if not any(_has_def_ex(e) for e in data):
        try:
            data = await ollama_enrich_vocab(data)
        except Exception as _enrich_err:
            logger.warning("ollama_enrich_vocab failed (preview keeps partial): %s", _enrich_err)
            enrich_warning = "AI definition generation failed — preview shows partial data. Please retry before saving."

    return {"parsed": data, **({"warning": enrich_warning} if enrich_warning else {})}


# @tag FILES @tag OCR @tag LEGACY
@router.post("/api/lessons/ingest_disk/{lesson}")
async def ingest_from_disk(lesson: str, force: bool = False, db: Session = Depends(get_db)):
    """OCR all images on disk for a lesson → data.json → DB sync.

    Skips OCR if data.json already exists (unless force=true).
    """
    lesson_key = _validate_lesson(lesson)
    dir_path = VOCA_ROOT / lesson_key

    if not dir_path.exists():
        raise HTTPException(status_code=404, detail=f"{lesson_key} 폴더 없음")

    data_json_path = dir_path / "data.json"

    if data_json_path.exists() and not force:
        existing = json.loads(data_json_path.read_text(encoding="utf-8"))
        if isinstance(existing, list) and existing:
            result = sync_lesson_to_db(
                db, VOCA_ROOT, lesson_key, existing,
                subject="English", textbook="Voca_8000",
                require_definition=False,  # existing on-disk data may be legacy
            )
            return {
                "lesson": lesson_key, "synced": result["synced"],
                "skipped_rows": result["skipped"],
                "words": len(existing), "images_processed": 0, "skipped": True,
            }

    IMAGE_EXTS = {".heic", ".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    image_files = sorted(
        p for p in dir_path.iterdir()
        if p.suffix.lower() in IMAGE_EXTS and not p.stem.lower().startswith("source")
    )
    if not image_files:
        raise HTTPException(status_code=404, detail="이미지 파일이 없습니다")

    all_data: list[dict] = []
    errors: list[str] = []

    for img_path in image_files:
        if img_path.suffix.lower() == ".heic":
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                subprocess.run(
                    ["sips", "-s", "format", "jpeg", str(img_path), "--out", str(tmp_path)],
                    check=True, capture_output=True,
                )
                raw = tmp_path.read_bytes()
            except subprocess.CalledProcessError:
                errors.append(f"{img_path.name}: HEIC 변환 실패")
                tmp_path.unlink(missing_ok=True)
                continue
            finally:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
        else:
            raw = img_path.read_bytes()

        try:
            data = await extract_vocab_from_bytes(raw)
            if data:
                all_data.extend(data)
            else:
                errors.append(f"{img_path.name}: OCR extracted no words")
        except Exception as e:
            errors.append(f"{img_path.name}: OCR 오류 - {e!s}")
            continue

    if not all_data:
        raise HTTPException(
            status_code=422,
            detail=f"OCR 실패 (전체 {len(image_files)}장). 오류: {'; '.join(errors)}",
        )

    seen: set[str] = set()
    unique_data: list[dict] = []
    for entry in all_data:
        w = (entry.get("word") or "").strip().lower()
        if w and w not in seen:
            seen.add(w)
            unique_data.append(entry)

    if not any(_has_def_ex(e) for e in unique_data):
        try:
            unique_data = await ollama_enrich_vocab(unique_data)
        except Exception as _enrich_err:
            logger.warning("ollama_enrich_vocab failed: %s", _enrich_err)
            raise HTTPException(
                status_code=422,
                detail="AI definition generation failed. Please retry — we won't save incomplete word data.",
            )

    (dir_path / "data.json").write_text(
        json.dumps(unique_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    result = sync_lesson_to_db(
        db, VOCA_ROOT, lesson_key, unique_data,
        subject="English", textbook="Voca_8000",
    )
    if result["synced"] == 0:
        raise HTTPException(
            status_code=422,
            detail=f"No valid words to save. Skipped {result['skipped']} rows: {'; '.join(result['reasons'][:3])}",
        )
    return {
        "lesson": lesson_key,
        "synced": result["synced"],
        "skipped": result["skipped"],
        "words": len(unique_data),
        "images_processed": len(image_files),
        "errors": errors,
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
