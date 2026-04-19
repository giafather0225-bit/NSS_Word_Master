"""
routers/diary_photo.py — Diary photo upload / serve / delete.
Section: Diary
Dependencies: models.py (DiaryEntry), database.py (LEARNING_ROOT)
API: POST /api/diary/photo, DELETE /api/diary/photo/{filename},
     GET /api/diary/photo/{filename}

Split from routers/diary.py to keep each file under the 300-line ceiling.
The literal `photo` segment must beat the catch-all
`/api/diary/{subject}/{textbook}` route, so this router MUST be registered
before routers/diary_sentences.py in main.py.
"""

import logging
import re as _re
import time as _time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from ..database import get_db, LEARNING_ROOT
    from ..models import DiaryEntry
except ImportError:
    from database import get_db, LEARNING_ROOT
    from models import DiaryEntry

router = APIRouter()
logger = logging.getLogger(__name__)

_PHOTO_DIR        = LEARNING_ROOT / "diary_photos"
_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
_PHOTO_EXTS       = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif"}
_PHOTO_MAX_BYTES  = 10_000_000  # 10 MB
_CHUNK_SIZE       = 1_048_576   # 1 MB
_PHOTO_NAME_RE    = _re.compile(r"^[A-Za-z0-9._-]+$")
_DATE_RE          = _re.compile(r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')


async def _stream_save_photo(file: UploadFile, dest: Path) -> int:
    """
    Stream an UploadFile to disk in 1 MB chunks, enforcing _PHOTO_MAX_BYTES.

    Mirrors routers/files.py::_stream_save_upload — a prior audit found that
    `await file.read()` on the whole body would pin the full 10 MB in RAM
    per concurrent uploader. Streaming caps peak memory at _CHUNK_SIZE and
    aborts early on oversized input (413), leaving no partial file behind.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > _PHOTO_MAX_BYTES:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Photo too large (max 10 MB)")
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Upload save failed: {exc!s}") from exc
    if total == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")
    return total


# @tag DIARY @tag JOURNAL
@router.post("/api/diary/photo", status_code=201)
async def upload_diary_photo(
    entry_date: str = Form(...),
    file:       UploadFile = File(...),
    db:         Session = Depends(get_db),
):
    """
    Attach a photo to the DiaryEntry for `entry_date`.

    Saves under LEARNING_ROOT/diary_photos/ with a deterministic name
    (date + epoch ms + ext) and stores the filename in DiaryEntry.photo_path.
    Creates a stub entry if none exists yet.
    """
    if not _DATE_RE.match(entry_date.strip()):
        raise HTTPException(status_code=400, detail="entry_date must be YYYY-MM-DD")

    ext = Path(file.filename or "upload.jpg").suffix.lower()
    if ext not in _PHOTO_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    safe_date = entry_date.strip()
    fname     = f"{safe_date}_{int(_time.time() * 1000)}{ext}"
    fpath     = _PHOTO_DIR / fname
    # Stream to disk — _stream_save_photo enforces size + empty-file checks
    # and cleans up the partial file on any failure.
    await _stream_save_photo(file, fpath)

    now_iso = datetime.now(timezone.utc).isoformat()
    entry = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.entry_date == safe_date)
        .first()
    )
    if entry:
        # Best-effort: delete prior file if it lived in our diary_photos dir
        old = (entry.photo_path or "").strip()
        if old and _PHOTO_NAME_RE.match(old):
            old_path = _PHOTO_DIR / old
            if old_path.exists() and old_path.parent == _PHOTO_DIR:
                try:
                    old_path.unlink()
                except OSError as exc:
                    logger.warning("Failed to remove old diary photo %s: %s", old_path, exc)
        entry.photo_path = fname
    else:
        entry = DiaryEntry(
            entry_date  = safe_date,
            content     = "",
            photo_path  = fname,
            created_at  = now_iso,
        )
        db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "entry_date": entry.entry_date,
        "photo_path": entry.photo_path,
        "photo_url":  f"/api/diary/photo/{entry.photo_path}",
    }


# @tag DIARY @tag JOURNAL
@router.delete("/api/diary/photo/{filename}")
def delete_diary_photo(filename: str, db: Session = Depends(get_db)):
    """Remove a diary photo file and clear its DB reference."""
    if not _PHOTO_NAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    fpath = _PHOTO_DIR / filename
    if fpath.exists() and fpath.parent == _PHOTO_DIR:
        try:
            fpath.unlink()
        except OSError as exc:
            logger.warning("Failed to delete diary photo %s: %s", fpath, exc)

    entry = db.query(DiaryEntry).filter(DiaryEntry.photo_path == filename).first()
    if entry:
        entry.photo_path = None
        db.commit()
    return {"deleted": filename}


# @tag DIARY @tag JOURNAL
@router.get("/api/diary/photo/{filename}")
def get_diary_photo(filename: str):
    """Serve a stored diary photo. Validates filename to prevent traversal."""
    if not _PHOTO_NAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    fpath = (_PHOTO_DIR / filename).resolve()
    if fpath.parent != _PHOTO_DIR.resolve() or not fpath.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(str(fpath))
