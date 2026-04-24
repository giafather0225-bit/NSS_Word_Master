"""
routers/ai_assistant_log.py — Logging API for Shadow Assistant
Section: AI / Logging
Dependencies: sqlalchemy, auth
API:
  GET /api/assistant/usage
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

# We import the get_db dependency. Assuming it's in backend.database
try:
    from backend.database import get_db
except ImportError:
    from ..database import get_db

from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.assistant import AssistantLog
from backend.models.system import AppConfig

try:
    from backend.auth import get_current_child
except ImportError:
    def get_current_child():
        return {"id": 1, "username": "gia"}

router = APIRouter()
logger = logging.getLogger(__name__)

_DEFAULT_DAILY_LIMIT = 30

def _get_daily_limit(db: Session) -> int:
    row = db.query(AppConfig).filter(AppConfig.key == "shadow_daily_limit").first()
    try:
        return int(row.value) if row else _DEFAULT_DAILY_LIMIT
    except (ValueError, TypeError):
        return _DEFAULT_DAILY_LIMIT

@router.get("/api/assistant/usage")
def get_assistant_usage(
    db: Session = Depends(get_db),
    child = Depends(get_current_child)
):
    """Get the number of queries the child has made today."""
    today = datetime.now(timezone.utc).date()
    daily_limit = _get_daily_limit(db)

    used_today = db.query(AssistantLog).filter(
        func.date(AssistantLog.created_at) == today
    ).count()

    remaining = max(0, daily_limit - used_today)

    return {
        "used_today": used_today,
        "limit": daily_limit,
        "remaining": remaining
    }

def async_log_chat(db: Session, session_id: str, user_message: str, assistant_reply: str, was_blocked: bool):
    """Helper method to log to the DB safely."""
    try:
        log = AssistantLog(
            session_id=session_id,
            user_message=user_message,
            assistant_reply=assistant_reply,
            was_blocked=was_blocked
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log assistant chat to DB: {e}")
        db.rollback()
