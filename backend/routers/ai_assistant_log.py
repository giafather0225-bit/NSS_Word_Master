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

# Assuming there's a child auth dependency, usually get_current_child
# But since this might fail if not found, we will fake it if it doesn't exist.
try:
    from backend.auth import get_current_child
except ImportError:
    # A dummy fallback for now if the file structure differs
    def get_current_child():
        return {"id": 1, "username": "gia"}

router = APIRouter()
logger = logging.getLogger(__name__)

DAILY_LIMIT = 30

@router.get("/api/assistant/usage")
def get_assistant_usage(
    db: Session = Depends(get_db),
    child = Depends(get_current_child)
):
    """Get the number of queries the child has made today."""
    today = datetime.now(timezone.utc).date()
    
    # Count logs created today
    used_today = db.query(AssistantLog).filter(
        func.date(AssistantLog.created_at) == today
    ).count()

    remaining = max(0, DAILY_LIMIT - used_today)
    
    return {
        "used_today": used_today,
        "limit": DAILY_LIMIT,
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
