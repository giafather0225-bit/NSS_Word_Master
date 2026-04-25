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

# Pillow + HEIC support — used after upload to (a) normalize EXIF rotation
# and (b) emit a 256×256 thumbnail next to the original. Imported lazily so
# a missing optional dep doesn't break the module-level import.
try:
    from PIL import Image, ImageOps
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    _PIL_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore
    ImageOps = None  # type: ignore
    _PIL_AVAILABLE = False

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


def _normalize_and_thumbnail(src: Path) -> Path | None:
    """
    Apply EXIF orientation + write a 256×256 thumbnail next to ``src``.

    Returns the thumbnail path on success, or None on any failure
    (PIL missing, format unsupported, decode error). Idempotent — calling
    twice on the same file just regenerates the thumb.

    Original file is rewritten in-place in JPEG/PNG/WebP. HEIC inputs are
    re-encoded to JPEG (HEIC isn't browser-friendly) and the source is
    replaced; the returned thumbnail uses the same final extension.
    """
    if not _PIL_AVAILABLE:
        return None
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)

            ext = src.suffix.lower()
            target_path = src
            save_format = None
            if ext in {".heic", ".heif"}:
                # Re-encode HEIC to JPEG so browsers can render it.
                target_path = src.with_suffix(".jpg")
                save_format = "JPEG"
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
            elif ext in {".jpg", ".jpeg"}:
                save_format = "JPEG"
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
            elif ext == ".png":
                save_format = "PNG"
            elif ext == ".webp":
                save_format = "WEBP"
            elif ext == ".gif":
                save_format = "GIF"

            if save_format:
                # Strip EXIF (which we already applied) so we don't keep stale
                # rotation hints + reduce metadata footprint.
                im.save(target_path, format=save_format, optimize=True)
                if target_path != src and src.exists():
                    src.unlink(missing_ok=True)

            # Thumbnail (256×256, contained, sharing target_path's extension).
            thumb_path = target_path.with_name(target_path.stem + "_thumb" + target_path.suffix)
            with Image.open(target_path) as t:
                t = ImageOps.exif_transpose(t)
                if t.mode in ("RGBA", "P") and target_path.suffix.lower() in {".jpg", ".jpeg"}:
                    t = t.convert("RGB")
                t.thumbnail((256, 256), Image.LANCZOS)
                t.save(thumb_path, format=save_format, optimize=True)
            return thumb_path
    except Exception as exc:  # noqa: BLE001 — best-effort post-processing
        logger.warning("Photo normalize/thumbnail failed for %s: %s", src, exc)
        return None


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

    # Normalize EXIF rotation + 256×256 thumbnail. HEIC is re-encoded to JPEG.
    _normalize_and_thumbnail(fpath)
    if ext in {".heic", ".heif"}:
        fname = Path(fname).with_suffix(".jpg").name

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
@router.post("/api/diary/photo/multi", status_code=201)
async def upload_diary_photo_multi(
    entry_date: str = Form(...),
    file:       UploadFile = File(...),
):
    """
    Save a single photo for the multi-photo Decorated diary.

    Unlike `POST /api/diary/photo`, this endpoint does NOT touch
    DiaryEntry.photo_path — the canonical store for multi-photo entries
    is `photos_json` (set on Save in routers/diary.py). Returns the URL
    so the client can include it in the snapshot.

    Files use a deterministic name (date + epoch ms + 4-char rand + ext)
    so concurrent uploads from the same date don't clash.
    """
    if not _DATE_RE.match(entry_date.strip()):
        raise HTTPException(status_code=400, detail="entry_date must be YYYY-MM-DD")

    ext = Path(file.filename or "upload.jpg").suffix.lower()
    if ext not in _PHOTO_EXTS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    import secrets
    rand = secrets.token_hex(2)
    fname = f"{entry_date.strip()}_{int(_time.time() * 1000)}_{rand}{ext}"
    fpath = _PHOTO_DIR / fname
    await _stream_save_photo(file, fpath)

    # EXIF rotate + 256×256 thumbnail. HEIC is re-encoded to JPEG so the
    # final filename may differ from what we wrote during streaming.
    thumb_path = _normalize_and_thumbnail(fpath)
    final_name = fname
    if ext in {".heic", ".heif"}:
        # _normalize_and_thumbnail rewrote the file as .jpg and removed the
        # original; surface the new filename to the client.
        final_name = Path(fname).with_suffix(".jpg").name
    thumb_name = thumb_path.name if thumb_path else None

    return {
        "filename":  final_name,
        "photo_url": f"/api/diary/photo/{final_name}",
        "thumb_url": f"/api/diary/photo/{thumb_name}" if thumb_name else None,
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

    # Companion thumbnail next to the original (named …_thumb.<ext>).
    thumb = fpath.with_name(fpath.stem + "_thumb" + fpath.suffix)
    if thumb.exists() and thumb.parent == _PHOTO_DIR:
        try:
            thumb.unlink()
        except OSError as exc:
            logger.warning("Failed to delete diary thumb %s: %s", thumb, exc)

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
