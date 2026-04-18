"""
routers/day_off.py — GIA's Day Off requests (child-side submission + listing).
Section: Diary
Dependencies: models.py (AppConfig, DayOffRequest), services/email_sender.py
API: POST /api/day-off/request, GET /api/day-off/requests

Parent-side approval/denial lives in routers/parent.py
(/api/parent/day-off-requests).
"""

import logging
import os
import re as _re
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, DayOffRequest
    from ..services.email_sender import send_email
except ImportError:
    from database import get_db
    from models import AppConfig, DayOffRequest
    from services.email_sender import send_email

router = APIRouter()
logger = logging.getLogger(__name__)

_DATE_RE = _re.compile(r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')


class DayOffRequestCreate(BaseModel):
    """Request body for submitting a day-off request."""
    request_date: str
    reason: str

    def clean(self) -> "DayOffRequestCreate":
        """Sanitize and validate fields."""
        self.request_date = self.request_date.strip()
        self.reason       = self.reason.strip()[:1000]
        if not _DATE_RE.match(self.request_date):
            raise HTTPException(status_code=400, detail="request_date must be YYYY-MM-DD")
        if not self.reason:
            raise HTTPException(status_code=400, detail="reason is required")
        return self


# @tag DIARY @tag DAY_OFF
def _get_parent_email(db: Session) -> str:
    """Look up parent email — env PARENT_EMAIL overrides AppConfig."""
    env = os.environ.get("PARENT_EMAIL", "").strip()
    if env:
        return env
    row = db.query(AppConfig).filter(AppConfig.key == "parent_email").first()
    return (row.value or "").strip() if row else ""


# @tag DIARY @tag DAY_OFF
@router.get("/api/day-off/requests")
def list_day_off_requests(db: Session = Depends(get_db)):
    """
    Return all DayOffRequest rows ordered by request_date DESC.

    Used by the diary "Day Off" section to render the user's history of
    pending / approved / denied requests.
    """
    rows = (
        db.query(DayOffRequest)
        .order_by(DayOffRequest.request_date.desc())
        .all()
    )
    return {
        "count": len(rows),
        "requests": [
            {
                "id":              r.id,
                "request_date":    r.request_date,
                "reason":          r.reason,
                "status":          r.status,
                "parent_response": r.parent_response,
                "created_at":      r.created_at,
            }
            for r in rows
        ],
    }


# @tag DIARY @tag DAY_OFF
@router.post("/api/day-off/request", status_code=201)
def create_day_off_request(
    req: DayOffRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a DayOffRequest and queue a parent-notification email.

    Returns 409 if a request already exists for that date so duplicates
    cannot be submitted. Email send is best-effort and never blocks
    the request response.
    """
    req.clean()

    duplicate = (
        db.query(DayOffRequest)
        .filter(DayOffRequest.request_date == req.request_date)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"A day-off request for {req.request_date} already exists (status: {duplicate.status})",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    day_off = DayOffRequest(
        request_date = req.request_date,
        reason       = req.reason,
        status       = "pending",
        created_at   = now_iso,
    )
    db.add(day_off)
    db.commit()
    db.refresh(day_off)

    parent_email = _get_parent_email(db)
    email_sent   = False
    if parent_email:
        subject = f"[GIA's Diary] Day Off Request — {day_off.request_date}"
        body = (
            "Hi,\n\n"
            "GIA submitted a Day Off request through the learning app.\n\n"
            f"Date:   {day_off.request_date}\n"
            f"Reason: {day_off.reason}\n\n"
            "Open the Parent Dashboard to approve or deny this request.\n\n"
            "— GIA Learning App"
        )
        background_tasks.add_task(send_email, parent_email, subject, body)
        email_sent = True

    return {
        "id":              day_off.id,
        "request_date":    day_off.request_date,
        "reason":          day_off.reason,
        "status":          day_off.status,
        "parent_response": day_off.parent_response,
        "created_at":      day_off.created_at,
        "email_queued":    email_sent,
    }
