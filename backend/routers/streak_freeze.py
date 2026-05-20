"""
routers/streak_freeze.py — Daily Streak Freeze API

Endpoints:
  GET  /api/streak/freeze/status   → {today, today_frozen, available_count}
  POST /api/streak/freeze          → consume one Streak Shield, freeze today

NOTE: Until backend/main.py is updated to `app.include_router(...)` this
router, the endpoints below are reachable only when imported and mounted
manually. Registration deferred to avoid colliding with a concurrent
session that has main.py checked out.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..services import streak_freeze_engine as freeze
except ImportError:  # pragma: no cover
    from database import get_db
    from services import streak_freeze_engine as freeze

router = APIRouter()


# @tag STREAK STREAK_FREEZE
@router.get("/api/streak/freeze/status")
def freeze_status(db: Session = Depends(get_db)) -> dict:
    """Return how many Streak Shields the child owns and whether today
    is already frozen."""
    return freeze.status(db)


# @tag STREAK STREAK_FREEZE
@router.post("/api/streak/freeze")
def freeze_today(db: Session = Depends(get_db)) -> dict:
    """Consume one Streak Shield and freeze today. 409 if today is
    already frozen; 400 if inventory is empty."""
    try:
        return freeze.apply_freeze(db)
    except freeze.FreezeError as exc:
        msg = str(exc)
        code = 409 if "already frozen" in msg.lower() else 400
        raise HTTPException(status_code=code, detail=msg)
