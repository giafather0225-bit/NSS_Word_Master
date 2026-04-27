"""
routers/parent_report.py — Weekly parent report API
Section: Parent
Dependencies: services/report_engine.py, services/email_sender.py
API: POST /api/parent/report/send      (PIN required)
     GET  /api/parent/report/preview   (PIN required)
     GET  /api/parent/report/schedule  (PIN required)
     POST /api/parent/report/schedule  (PIN required)
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
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
    child_name:  str  = "Gia"


def _cfg(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else default


# ── Send now ──────────────────────────────────────────────

@router.post("/api/parent/report/send")
def send_report_now(
    background_tasks: BackgroundTasks,
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """즉시 주간 리포트 이메일 발송. @tag PARENT REPORT"""
    email = _cfg(db, "parent_email")
    if not email or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="parent_email not configured. Set it in Parent Settings.",
        )
    child_name = _cfg(db, "report_child_name", "Gia")
    background_tasks.add_task(report_engine.send_weekly_report, db, email, child_name)
    return {"ok": True, "message": f"Report queued to {email}"}


# ── Preview (JSON) ────────────────────────────────────────

@router.get("/api/parent/report/preview")
def preview_report(
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """리포트 데이터 JSON 미리보기. @tag PARENT REPORT"""
    return report_engine.collect_weekly_data(db)


# ── Schedule ──────────────────────────────────────────────

@router.get("/api/parent/report/schedule")
def get_schedule(
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """자동 발송 스케줄 조회. @tag PARENT REPORT"""
    return {
        "enabled":      _cfg(db, "report_enabled",     "0") == "1",
        "day_of_week":  int(_cfg(db, "report_day_of_week", "1")),
        "child_name":   _cfg(db, "report_child_name",  "Gia"),
        "parent_email": _cfg(db, "parent_email",       ""),
    }


@router.post("/api/parent/report/schedule")
def set_schedule(
    body: ReportScheduleIn,
    db:   Session = Depends(get_db),
    _pin: bool    = Depends(require_parent_pin),
):
    """자동 발송 스케줄 저장. @tag PARENT REPORT"""
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
