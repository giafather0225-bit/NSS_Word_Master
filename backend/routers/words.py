"""
routers/words.py — Lesson word CRUD and storage retrieval
Section: English
Dependencies: database, models
API:
  POST   /api/words/lesson/{lesson_id}
  PATCH  /api/words/lesson/{lesson_id}/{word_id}
  DELETE /api/words/lesson/{lesson_id}/{word_id}
  GET    /api/storage/lessons/{lesson_id}/words
"""
from typing import Optional

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Lesson, StudyItem, Word
from backend.schemas_common import Str20, Str100, Str500

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Pydantic Schemas ───────────────────────────────────────

class ManualWordCreate(BaseModel):
    word: Str100
    definition: Str500
    example: Str500 = ""
    pos: Str20 = ""

    def clean(self):
        """No-op — length/strip enforced by Pydantic (422 on overflow)."""
        return self


class ManualWordUpdate(BaseModel):
    definition: Optional[Str500] = None
    example:    Optional[Str500] = None
    pos:        Optional[Str20] = None

    def clean(self):
        """No-op — length/strip enforced by Pydantic (422 on overflow)."""
        return self


# ── Helpers ────────────────────────────────────────────────

def _serialize_word(w: Word) -> dict:
    """Serialize a Word ORM row to a plain dict."""
    return {
        "id":            w.id,
        "word":          w.word,
        "pos":           w.pos,
        "definition":    w.definition,
        "example":       w.example,
        "source_type":   w.source_type,
        "study_item_id": w.study_item_id,
        "created_at":    w.created_at,
    }


# ── Routes ─────────────────────────────────────────────────

# @tag WORDS @tag MANUAL
@router.post("/api/words/lesson/{lesson_id}", status_code=201)
def create_manual_word(
    lesson_id: int,
    body: ManualWordCreate,
    db: Session = Depends(get_db),
):
    """Add a manually typed word to lesson_id (source_type='manual'); saves to words + study_items."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} not found")

    req = body.clean()

    if db.query(Word).filter(Word.lesson_id == lesson_id, Word.word == req.word).first():
        raise HTTPException(
            status_code=409,
            detail=f"'{req.word}' already exists in lesson_id={lesson_id}",
        )

    now = datetime.now(timezone.utc).isoformat()
    extra = json.dumps({"pos": req.pos}, ensure_ascii=False)

    study_item = StudyItem(
        subject=lesson.subject,
        textbook=lesson.textbook,
        lesson=lesson.lesson_name,
        lesson_id=lesson_id,
        source_type="manual",
        question=req.definition,
        answer=req.word,
        hint=req.example,
        extra_data=extra,
    )
    db.add(study_item)
    db.flush()

    word_obj = Word(
        word=req.word,
        definition=req.definition,
        example=req.example,
        pos=req.pos,
        lesson_id=lesson_id,
        study_item_id=study_item.id,
        source_type="manual",
        ocr_engine="",
        created_at=now,
    )
    db.add(word_obj)
    db.commit()
    db.refresh(word_obj)

    return _serialize_word(word_obj)


# @tag WORDS @tag MANUAL
@router.patch("/api/words/lesson/{lesson_id}/{word_id}")
def update_manual_word(
    lesson_id: int,
    word_id: int,
    body: ManualWordUpdate,
    db: Session = Depends(get_db),
):
    """Update definition/example/pos for a stored word and sync to study_items."""
    word_obj = db.query(Word).filter(Word.id == word_id, Word.lesson_id == lesson_id).first()
    if not word_obj:
        raise HTTPException(status_code=404, detail=f"word_id={word_id} not found")

    req = body.clean()
    if req.definition is not None:
        word_obj.definition = req.definition
    if req.example is not None:
        word_obj.example = req.example
    if req.pos is not None:
        word_obj.pos = req.pos

    if word_obj.study_item_id:
        item = db.query(StudyItem).filter(StudyItem.id == word_obj.study_item_id).first()
        if item:
            if req.definition is not None:
                item.question = req.definition
            if req.example is not None:
                item.hint = req.example
            if req.pos is not None:
                extra = json.loads(item.extra_data or "{}")
                extra["pos"] = req.pos
                item.extra_data = json.dumps(extra, ensure_ascii=False)

    db.commit()
    db.refresh(word_obj)
    return _serialize_word(word_obj)


# @tag WORDS @tag MANUAL
@router.delete("/api/words/lesson/{lesson_id}/{word_id}", status_code=204)
def delete_manual_word(
    lesson_id: int,
    word_id: int,
    db: Session = Depends(get_db),
):
    """Delete a word (and its linked study_item) from a lesson."""
    word_obj = db.query(Word).filter(Word.id == word_id, Word.lesson_id == lesson_id).first()
    if not word_obj:
        raise HTTPException(status_code=404, detail=f"word_id={word_id} not found")

    if word_obj.study_item_id:
        item = db.query(StudyItem).filter(StudyItem.id == word_obj.study_item_id).first()
        if item:
            db.delete(item)

    db.delete(word_obj)
    db.commit()


# @tag WORDS @tag STORAGE
@router.get("/api/storage/lessons/{lesson_id}/words")
def get_lesson_words(lesson_id: int, db: Session = Depends(get_db)):
    """Return all words stored in the words table for a given lesson_id."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} not found")

    words = (
        db.query(Word)
        .filter(Word.lesson_id == lesson_id)
        .order_by(Word.id)
        .all()
    )
    return {
        "lesson_id":   lesson_id,
        "lesson_name": lesson.lesson_name,
        "words": [
            {
                "id":           w.id,
                "word":         w.word,
                "pos":          w.pos,
                "definition":   w.definition,
                "example":      w.example,
                "ocr_engine":   w.ocr_engine,
                "study_item_id": w.study_item_id,
                "created_at":   w.created_at,
            }
            for w in words
        ],
        "count": len(words),
    }
