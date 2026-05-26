"""
routers/starred.py — Starred (favourited) study items API
Section: English
Dependencies: models (StudyItem), database
API: PATCH /api/study-items/{item_id}/star   — toggle star
     GET   /api/study-items/starred          — list all starred items
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import StudyItem

logger = logging.getLogger(__name__)
router = APIRouter()


def _serialize(item: StudyItem) -> dict:
    return {
        "id":         item.id,
        "word":       item.answer   or "",  # answer = correct spelling
        "meaning":    item.question or "",  # question = definition
        "example":    item.hint     or "",  # hint = example sentence
        "lesson":     item.lesson,
        "textbook":   item.textbook,
        "is_starred": bool(item.is_starred),
    }


@router.patch("/api/study-items/{item_id}/star")
def toggle_star(item_id: int, db: Session = Depends(get_db)):
    """Toggle star/favourite on a study item. @tag ENGLISH ACADEMY"""
    item = db.query(StudyItem).filter(StudyItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Study item not found")
    item.is_starred = 0 if item.is_starred else 1
    db.commit()
    db.refresh(item)
    return {"ok": True, "is_starred": bool(item.is_starred), "item": _serialize(item)}


@router.get("/api/study-items/starred")
def list_starred(db: Session = Depends(get_db)):
    """Return all starred study items ordered by textbook, lesson, word. @tag ENGLISH ACADEMY"""
    items = (
        db.query(StudyItem)
        .filter(StudyItem.is_starred == 1)
        .order_by(StudyItem.textbook, StudyItem.lesson, StudyItem.answer)
        .all()
    )
    return {"count": len(items), "items": [_serialize(i) for i in items]}
