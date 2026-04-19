"""
routers/free_writing.py — GIA's Diary "Free Writing" section.
Section: Diary
Dependencies: models.py (FreeWriting), routers/diary.py (_get_grammar_feedback)
API: GET /api/free-writing/entries, POST /api/free-writing/entries,
     DELETE /api/free-writing/entries/{id}
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import FreeWriting
    from ..schemas_common import Str120, Str10000
    from .diary import _get_grammar_feedback
except ImportError:
    from database import get_db
    from models import FreeWriting
    from schemas_common import Str120, Str10000
    from routers.diary import _get_grammar_feedback

router = APIRouter()


class FreeWritingCreate(BaseModel):
    """Request body for creating a free-writing entry."""
    title: Str120
    content: Str10000

    def clean(self) -> "FreeWritingCreate":
        """Validate non-empty (length enforced by Pydantic — 422 on overflow)."""
        if not self.title:
            raise HTTPException(status_code=400, detail="title is required")
        if not self.content:
            raise HTTPException(status_code=400, detail="content is required")
        return self


def _serialize(row: FreeWriting) -> dict:
    """Convert a FreeWriting row to a JSON-safe dict."""
    return {
        "id":          row.id,
        "title":       row.title,
        "content":     row.content,
        "ai_feedback": row.ai_feedback,
        "created_at":  row.created_at,
    }


# @tag DIARY @tag JOURNAL
@router.get("/api/free-writing/entries")
def list_free_writing(db: Session = Depends(get_db)) -> dict:
    """Return all free-writing entries, newest first."""
    rows = (
        db.query(FreeWriting)
        .order_by(FreeWriting.created_at.desc(), FreeWriting.id.desc())
        .all()
    )
    return {"count": len(rows), "entries": [_serialize(r) for r in rows]}


# @tag DIARY @tag JOURNAL @tag AI
@router.post("/api/free-writing/entries", status_code=201)
async def create_free_writing(
    req: FreeWritingCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Create a free-writing entry and attach AI grammar feedback."""
    req.clean()
    feedback = await _get_grammar_feedback(req.content)
    row = FreeWriting(
        title       = req.title,
        content     = req.content,
        ai_feedback = feedback,
        created_at  = datetime.now(timezone.utc).isoformat(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row)


# @tag DIARY @tag JOURNAL
@router.delete("/api/free-writing/entries/{entry_id}")
def delete_free_writing(entry_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete a free-writing entry by id."""
    row = db.query(FreeWriting).filter(FreeWriting.id == entry_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(row)
    db.commit()
    return {"deleted": entry_id}
