"""
routers/parent_xp.py — Parent Dashboard XP Rules & Report endpoints
Section: Parent
Dependencies: models.py (AppConfig, XPLog), services/xp_engine.py,
              routers/parent.py (shared PIN dep)
API: GET  /api/parent/xp-rules
     POST /api/parent/xp-rules        (PIN)
     POST /api/parent/xp-rules/reset  (PIN)
     GET  /api/parent/xp-report
"""

from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, XPLog
    from ..services import xp_engine
    from .parent import require_parent_pin, _upsert_app_config
except ImportError:
    from database import get_db
    from models import AppConfig, XPLog
    from services import xp_engine
    from routers.parent import require_parent_pin, _upsert_app_config


router = APIRouter()


class XPRulesIn(BaseModel):
    rules:            dict[str, int] | None = None
    arcade_daily_cap: int            | None = None


@router.get("/api/parent/xp-rules")
def parent_xp_rules(db: Session = Depends(get_db)):
    """Return current effective XP rules + defaults + arcade cap. @tag PARENT XP SETTINGS"""
    return {
        "rules":              xp_engine.get_xp_rules(db),
        "defaults":           dict(xp_engine.XP_RULES_DEFAULT),
        "arcade_daily_cap":   xp_engine.get_arcade_daily_cap(db),
        "arcade_cap_default": xp_engine.ARCADE_DAILY_CAP_DEFAULT,
    }


@router.post("/api/parent/xp-rules")
def parent_xp_rules_save(
    body: XPRulesIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Save XP rule overrides. Unknown actions are rejected. @tag PARENT XP SETTINGS"""
    now = datetime.now().isoformat()
    valid = set(xp_engine.XP_RULES_DEFAULT.keys())

    if body.rules:
        for action, value in body.rules.items():
            if action not in valid:
                raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
            if not isinstance(value, int) or value < 0 or value > 10_000:
                raise HTTPException(status_code=400, detail=f"Invalid value for {action}")
            _upsert_app_config(db, f"xp_rule_{action}", str(value), now)

    if body.arcade_daily_cap is not None:
        cap = body.arcade_daily_cap
        if not isinstance(cap, int) or cap < 0 or cap > 1000:
            raise HTTPException(status_code=400, detail="Invalid arcade_daily_cap")
        _upsert_app_config(db, "arcade_daily_cap", str(cap), now)

    db.commit()
    return {"ok": True}


@router.post("/api/parent/xp-rules/reset")
def parent_xp_rules_reset(
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Delete all xp_rule_* overrides and arcade_daily_cap. @tag PARENT XP SETTINGS"""
    (db.query(AppConfig)
       .filter((AppConfig.key.like("xp_rule_%")) | (AppConfig.key == "arcade_daily_cap"))
       .delete(synchronize_session=False))
    db.commit()
    return {"ok": True}


@router.get("/api/parent/xp-report")
def parent_xp_report(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Per-day XP totals + per-action breakdown over last N days. @tag PARENT XP REPORT"""
    today = date.today()
    start = (today - timedelta(days=days - 1)).isoformat()

    day_rows = (
        db.query(XPLog.earned_date, func.sum(XPLog.xp_amount))
        .filter(XPLog.earned_date >= start)
        .group_by(XPLog.earned_date)
        .all()
    )
    day_map = {d: int(total or 0) for d, total in day_rows}
    daily = []
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()
        daily.append({"date": d, "xp": day_map.get(d, 0)})

    action_rows = (
        db.query(XPLog.action, func.sum(XPLog.xp_amount), func.count(XPLog.id))
        .filter(XPLog.earned_date >= start)
        .group_by(XPLog.action)
        .order_by(func.sum(XPLog.xp_amount).desc())
        .all()
    )
    by_action = [
        {"action": a, "xp": int(total or 0), "count": int(cnt or 0)}
        for a, total, cnt in action_rows
    ]

    total = sum(r["xp"] for r in daily)
    return {"days": days, "total_xp": total, "daily": daily, "by_action": by_action}
