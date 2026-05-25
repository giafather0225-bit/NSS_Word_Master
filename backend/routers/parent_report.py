"""
routers/parent_report.py — Weekly parent report API
Section: Parent
Dependencies: services/report_engine.py, services/email_sender.py
API: POST /api/parent/report/send      (PIN required)
     GET  /api/parent/report/preview   (PIN required)
     GET  /api/parent/report/schedule  (PIN required)
     POST /api/parent/report/schedule  (PIN required)
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AppConfig
from backend.routers.parent import require_parent_pin, _upsert_app_config
from backend.services import report_engine

logger = logging.getLogger(__name__)
router = APIRouter()


class ReportScheduleIn(BaseModel):
    enabled:     bool = True
    day_of_week: int  = 1      # 0=Mon … 6=Sun
    child_name:  str  = Field(default="Gia", max_length=50)


def _cfg(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else default


def _bulk_cfg(db: Session, keys: list[str], defaults: dict[str, str] | None = None) -> dict[str, str]:
    """Load multiple AppConfig keys in a single IN query. Faster than repeated _cfg() calls."""
    rows = db.query(AppConfig).filter(AppConfig.key.in_(keys)).all()
    result = {k: (defaults or {}).get(k, "") for k in keys}
    for row in rows:
        result[row.key] = row.value
    return result


# ── Send now ──────────────────────────────────────────────

@router.post("/api/parent/report/send")
def send_report_now(
    background_tasks: BackgroundTasks,
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """Send the weekly report email immediately. @tag PARENT REPORT"""
    cfg = _bulk_cfg(db, ["parent_email", "report_child_name"], {"report_child_name": "Gia"})
    email = cfg["parent_email"]
    if not email or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="parent_email not configured. Set it in Parent Settings.",
        )
    child_name = cfg["report_child_name"]
    background_tasks.add_task(report_engine.send_weekly_report, db, email, child_name)
    return {"ok": True, "message": f"Report queued to {email}"}


# ── Preview (JSON) ────────────────────────────────────────

@router.get("/api/parent/report/preview")
def preview_report(
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """Return a JSON preview of the weekly report data. @tag PARENT REPORT"""
    return report_engine.collect_weekly_data(db)


# ── Schedule ──────────────────────────────────────────────

@router.get("/api/parent/report/schedule")
def get_schedule(
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """Get the current automatic report send schedule. @tag PARENT REPORT"""
    cfg = _bulk_cfg(db, ["report_enabled", "report_day_of_week", "report_child_name", "parent_email"],
                    {"report_enabled": "0", "report_day_of_week": "1", "report_child_name": "Gia"})
    return {
        "enabled":      cfg["report_enabled"] == "1",
        "day_of_week":  int(cfg["report_day_of_week"]),
        "child_name":   cfg["report_child_name"],
        "parent_email": cfg["parent_email"],
    }


@router.post("/api/parent/report/schedule")
def set_schedule(
    body: ReportScheduleIn,
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """Save the automatic report send schedule. @tag PARENT REPORT"""
    if not 0 <= body.day_of_week <= 6:
        raise HTTPException(status_code=400, detail="day_of_week must be 0–6")
    if not body.child_name.strip():
        raise HTTPException(status_code=400, detail="child_name required")
    now = datetime.now().isoformat()
    _upsert_app_config(db, "report_enabled",     "1" if body.enabled else "0", now)
    _upsert_app_config(db, "report_day_of_week", str(body.day_of_week),        now)
    _upsert_app_config(db, "report_child_name",  body.child_name.strip(),      now)
    db.commit()
    return {"ok": True}
