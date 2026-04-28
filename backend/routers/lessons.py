"""
routers/lessons.py — Lesson/subject/textbook directory and metadata routes
Section: English / System
Dependencies: database, models, voca_sync
API:
  GET  /api/subjects
  GET  /api/textbooks/{subject}
  GET  /api/lessons/{subject}/{textbook}
  GET  /api/lessons
  GET  /api/lesson-lookup
  POST /api/voca/create-lesson/{lesson}
  GET  /api/voca/folders
  GET  /api/voca/folder-detail/{lesson}
  DELETE /api/voca/folder/{lesson}
"""

import json as _json
import logging
import re as _re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as _text
from sqlalchemy.orm import Session

from backend.database import get_db, LEARNING_ROOT
from backend.models import Lesson, StudyItem
from backend.utils import validate_lesson as _validate_lesson, validate_name as _validate_name

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Constants ──────────────────────────────────────────────
VOCA_ROOT = LEARNING_ROOT / "English" / "Voca_8000"

# Canonical subjects exposed by the app. LEARNING_ROOT is co-located with
# backup/storage/app dirs, so filesystem listing alone is not authoritative.
SUBJECTS = ("English", "Math")

# _validate_lesson, _validate_name → backend/utils.py


# ── Routes ─────────────────────────────────────────────────

# @tag LESSONS @tag SUBJECTS
@router.get("/api/subjects")
def list_subjects():
    """Return list of subject (top-level) folders under ~/NSS_Learning/."""
    LEARNING_ROOT.mkdir(parents=True, exist_ok=True)
    subjects = [s for s in SUBJECTS if (LEARNING_ROOT / s).is_dir()]
    return {"subjects": subjects}


# @tag LESSONS @tag TEXTBOOKS
@router.get("/api/textbooks/{subject}")
def list_textbooks(subject: str):
    """Return list of textbook folders under ~/NSS_Learning/{subject}/."""
    subject_key = _validate_name(subject, "subject")
    subject_dir = LEARNING_ROOT / subject_key
    if not subject_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Subject '{subject_key}' not found")
    names = [
        p.name for p in subject_dir.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    # Sort Voca_NNNN numerically by NNNN, then everything else alphabetically after.
    def _sort_key(n: str):
        m = _re.match(r'^Voca_(\d+)$', n)
        return (0, int(m.group(1))) if m else (1, n.lower())
    textbooks = sorted(names, key=_sort_key)
    return {"subject": subject_key, "textbooks": textbooks}


# @tag LESSONS
@router.get("/api/lessons/{subject}/{textbook}")
def list_lessons_by_textbook(subject: str, textbook: str):
    """Return list of lesson folders under ~/NSS_Learning/{subject}/{textbook}/."""
    subject_key  = _validate_name(subject, "subject")
    textbook_key = _validate_name(textbook, "textbook")
    textbook_dir = LEARNING_ROOT / subject_key / textbook_key
    if not textbook_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Textbook '{textbook_key}' not found")
    lessons = []
    for p in sorted(textbook_dir.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            lessons.append({"name": p.name, "ready": (p / "data.json").is_file()})
    return {"subject": subject_key, "textbook": textbook_key, "lessons": lessons}


# @tag LESSONS @tag LEGACY
@router.get("/api/lessons")
def list_lessons():
    """Return lesson list for the default Voca_8000 textbook (legacy compat)."""
    VOCA_ROOT.mkdir(parents=True, exist_ok=True)
    lessons = []
    for p in sorted(VOCA_ROOT.iterdir()):
        if not p.is_dir():
            continue
        has_data = (p / "data.json").is_file()
        lessons.append({"name": p.name, "ready": has_data})
    return {"lessons": lessons}


# @tag LESSONS @tag LOOKUP
@router.get("/api/lesson-lookup")
def lesson_lookup(
    subject: str,
    textbook: str = "",
    lesson: str = "",
    db: Session = Depends(get_db),
):
    """Look up or auto-create a lesson row by (subject, textbook, lesson_name).

    Used by Word Manager to obtain a lesson_id.
    """
    subject_key  = _validate_name(subject, "subject")
    lesson_key   = _validate_lesson(lesson) if lesson else ""
    textbook_key = textbook.strip()

    row = (
        db.query(Lesson)
        .filter(
            Lesson.subject     == subject_key,
            Lesson.textbook    == textbook_key,
            Lesson.lesson_name == lesson_key,
        )
        .first()
    )

    if not row:
        # INSERT OR IGNORE 패턴 — 동시 요청 race condition 방지.
        # 두 요청이 동시에 first()=None을 보고 insert를 시도할 때
        # 두 번째 insert가 IntegrityError를 내면 기존 row를 반환한다.
        try:
            row = Lesson(
                subject=subject_key,
                textbook=textbook_key,
                lesson_name=lesson_key,
                source_type="manual",
                description="",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
        except Exception:
            db.rollback()
            row = (
                db.query(Lesson)
                .filter(
                    Lesson.subject     == subject_key,
                    Lesson.textbook    == textbook_key,
                    Lesson.lesson_name == lesson_key,
                )
                .first()
            )
            if not row:
                raise HTTPException(status_code=500, detail="lesson_lookup: insert conflict")

    return {
        "id":          row.id,
        "subject":     row.subject,
        "textbook":    row.textbook,
        "lesson_name": row.lesson_name,
        "source_type": row.source_type,
    }


# @tag LESSONS @tag VOCA
@router.post("/api/voca/create-lesson/{lesson}")
def create_voca_lesson(lesson: str, textbook: str = "Voca_8000"):
    """Create an empty lesson folder under English/{textbook}/."""
    lesson_key = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / textbook / lesson_key
    lesson_dir.mkdir(parents=True, exist_ok=True)
    return {"created": True, "lesson": lesson_key, "path": str(lesson_dir)}


# @tag LESSONS @tag VOCA @tag FOLDERS
@router.get("/api/voca/folders")
def list_voca_folders(textbook: str = "Voca_8000"):
    """Return folder list with image counts and word counts for English/{textbook}/."""
    root = LEARNING_ROOT / "English" / textbook
    if not root.is_dir():
        return {"folders": []}
    folders = []
    for p in sorted(root.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        images = [f.name for f in p.iterdir()
                  if f.suffix.lower() in (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
                  and not f.name.startswith(".")]
        data_json = p / "data.json"
        word_count = 0
        if data_json.is_file():
            try:
                word_count = len(_json.loads(data_json.read_text("utf-8")))
            except Exception as exc:
                logger.warning("Failed to parse data.json in %s: %s", p, exc)
        folders.append({
            "name": p.name,
            "image_count": len(images),
            "word_count": word_count,
            "has_data": data_json.is_file(),
        })
    return {"root": str(root), "folders": folders}


# @tag LESSONS @tag VOCA @tag FOLDERS
@router.get("/api/voca/folder-detail/{lesson}")
def voca_folder_detail(lesson: str, textbook: str = "Voca_8000"):
    """Return images and words for a specific lesson folder."""
    lesson_key = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / textbook / lesson_key
    if not lesson_dir.is_dir():
        lesson_dir.mkdir(parents=True, exist_ok=True)

    all_files = sorted(
        f for f in lesson_dir.iterdir()
        if f.suffix.lower() in (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
        and not f.name.startswith(".")
    )
    heic_stems = {f.stem for f in all_files if f.suffix.lower() in (".heic", ".heif")}
    images = []
    for f in all_files:
        # Skip JPG if a matching HEIC exists (leftover from conversion)
        if f.suffix.lower() in (".jpg", ".jpeg") and f.stem in heic_stems:
            continue
        images.append({"name": f.name, "size": f.stat().st_size, "ext": f.suffix.lower()})

    words = []
    data_json = lesson_dir / "data.json"
    if data_json.is_file():
        try:
            words = _json.loads(data_json.read_text("utf-8"))
        except Exception as exc:
            logger.warning("Failed to parse data.json for %s: %s", lesson_dir, exc)

    return {
        "lesson": lesson_key,
        "path": str(lesson_dir),
        "images": images,
        "image_count": len(images),
        "words": words,
        "word_count": len(words),
    }


# @tag LESSONS @tag VOCA @tag FOLDERS
@router.delete("/api/voca/folder/{lesson}")
def delete_voca_folder(lesson: str, textbook: str = "Voca_8000", db: Session = Depends(get_db)):
    """Delete a lesson folder and its DB records."""
    lesson_key = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / textbook / lesson_key
    if not lesson_dir.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")
    shutil.rmtree(lesson_dir)
    db.execute(
        _text("DELETE FROM study_items WHERE lesson = :l AND subject = 'English'"),
        {"l": lesson_key},
    )
    db.commit()
    return {"deleted": True, "lesson": lesson_key}
