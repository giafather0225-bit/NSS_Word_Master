"""
routers/parent.py — Parent Dashboard core: PIN, task settings, schedule,
                    config, day-off, shared helpers.

Stats (overview/summary/activity/stage-stats/word-stats) → parent_stats.py
Math summary                                              → parent_math.py
Streak (3 endpoints)                                      → parent_streak.py
XP rules & report (4 endpoints)                           → parent_xp.py

Section: Parent
Dependencies: models.py (AppConfig, TaskSetting, AcademySchedule, DayOffRequest)
API: POST /api/parent/verify-pin
     GET/PUT /api/parent/task-settings[/{key}]
     GET/POST /api/parent/academy-schedule
     GET /api/parent/config/{key}, POST /api/parent/config
     GET/PUT /api/parent/day-off-requests[/{id}]
"""

import logging
import re
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import AppConfig, TaskSetting, AcademySchedule, DayOffRequest
    from ..services import pin_guard, pin_hash
except ImportError:
    from database import get_db
    from models import AppConfig, TaskSetting, AcademySchedule, DayOffRequest
    from services import pin_guard, pin_hash

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_PIN = "0000"
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ─── Schemas ──────────────────────────────────────────────────

# Input validation bounds — keeps a malicious or typo'd Parent UI from
# writing values that would break the child's experience (e.g. negative XP
# or a weekday number of 99).

class TaskSettingUpdate(BaseModel):
    is_required: bool | None = None
    # XP for any single task is bounded [0, 1000]. Zero disables rewarding
    # without deleting the row; 1000 is a soft upper bound well above the
    # highest documented rule (streak_30_bonus = 200).
    xp_value:    int  | None = Field(default=None, ge=0, le=1000)
    is_active:   bool | None = None


class AcademyScheduleIn(BaseModel):
    # 0=Mon … 6=Sun. Pydantic Field bounds reject day=99 before it hits SQL.
    days: list[int] = Field(default_factory=list)
    memo: str = Field(default="", max_length=200)


class ConfigIn(BaseModel):
    # Whitelist enforced in the endpoint; still bound sizes at the schema.
    key:   str = Field(min_length=1, max_length=64)
    value: str = Field(max_length=500)


class DayOffDecisionIn(BaseModel):
    status:          str   # validated in-route ("approved" | "denied")
    parent_response: str = Field(default="", max_length=500)


class PinVerifyIn(BaseModel):
    pin: str = Field(min_length=1, max_length=16)


# ─── PIN verification ──────────────────────────────────────────

def _get_stored_pin(db: Session) -> str:
    """Read the active parent PIN row from AppConfig, falling back to DEFAULT_PIN.

    The value may be either a pbkdf2 hash (preferred) or — on databases that
    predate the hashing rollout — the literal 4-digit string. Callers must
    verify via `pin_hash.verify_pin`, not raw compare, so both formats work.
    """
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    return row.value if (row and row.value) else DEFAULT_PIN


def _upgrade_pin_if_plaintext(db: Session, verified_pin: str) -> None:
    """After a successful verify, rewrite a legacy plaintext row as a hash.

    Idempotent: a no-op once the stored value is already hashed. Runs in the
    verify path so the migration happens the first time a parent enters the
    correct PIN — no manual step, no downtime, and an intruder who never
    knows the PIN can't trigger an upgrade to cover their tracks.
    """
    row = db.query(AppConfig).filter(AppConfig.key == "pin").first()
    if not row or not pin_hash.needs_upgrade(row.value or ""):
        return
    row.value = pin_hash.hash_pin(verified_pin)
    row.updated_at = datetime.now().isoformat()
    db.commit()


# @tag PARENT PIN
def require_parent_pin(
    x_parent_pin: str | None = Header(default=None, alias="X-Parent-Pin"),
    db: Session = Depends(get_db),
) -> bool:
    """
    FastAPI dependency that guards parent mutation endpoints.

    Frontend MUST send the verified PIN in the `X-Parent-Pin` request header
    on every mutating call (PUT/POST). The PIN is checked against AppConfig
    and rejected with 403 if missing or wrong. Read-only GET endpoints can
    still be called without a PIN — only mutations require it.

    This closes the gap where /api/parent/config etc. previously accepted
    any unauthenticated caller and could even let the child reset their own
    parent PIN via the browser console.
    """
    pin_guard.assert_not_locked(db, "parent")
    stored = _get_stored_pin(db)
    if not x_parent_pin or not pin_hash.verify_pin(x_parent_pin, stored):
        pin_guard.record_failure(db, "parent")
        raise HTTPException(status_code=403, detail="Parent PIN required")
    # Don't call record_success() on every mutating request — only on the
    # explicit verify endpoint — or we'd hit the DB on every write.
    return True


@router.post("/api/parent/verify-pin")
def parent_verify_pin(body: PinVerifyIn, db: Session = Depends(get_db)):
    """
    Verify the parent PIN. Returns ok:true on success.
    Rate-limited: 5 wrong attempts → 5 minute lockout. @tag PARENT PIN SECURITY
    """
    pin_guard.assert_not_locked(db, "parent")
    stored = _get_stored_pin(db)
    if not pin_hash.verify_pin(body.pin or "", stored):
        pin_guard.record_failure(db, "parent")
        raise HTTPException(status_code=403, detail="Wrong PIN")
    pin_guard.record_success(db, "parent")
    _upgrade_pin_if_plaintext(db, body.pin or "")
    return {"ok": True}


# ─── Task Settings ────────────────────────────────────────────

@router.get("/api/parent/task-settings")
def parent_task_settings(db: Session = Depends(get_db)):
    """Return all task settings. @tag PARENT SETTINGS"""
    tasks = db.query(TaskSetting).order_by(TaskSetting.id).all()
    return {"tasks": [{"task_key": t.task_key, "is_required": t.is_required,
                        "xp_value": t.xp_value, "is_active": t.is_active} for t in tasks]}


@router.put("/api/parent/task-settings/{key}")
def parent_update_task(
    key: str,
    body: TaskSettingUpdate,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Update a task setting. PIN-protected. @tag PARENT SETTINGS"""
    task = db.query(TaskSetting).filter(TaskSetting.task_key == key).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.is_required is not None: task.is_required = body.is_required
    if body.xp_value    is not None: task.xp_value    = body.xp_value
    if body.is_active   is not None: task.is_active   = body.is_active
    db.commit()
    return {"ok": True}


# ─── Academy Schedule ─────────────────────────────────────────

@router.get("/api/parent/academy-schedule")
def parent_get_schedule(db: Session = Depends(get_db)):
    """Return active academy schedule days. @tag PARENT SCHEDULE"""
    rows = db.query(AcademySchedule).filter(AcademySchedule.is_active == True).all()
    return {"days": [{"day_of_week": r.day_of_week, "memo": r.memo or ""} for r in rows]}


@router.post("/api/parent/academy-schedule")
def parent_set_schedule(
    body: AcademyScheduleIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Replace academy schedule with new day list. PIN-protected. @tag PARENT SCHEDULE"""
    # Reject out-of-range day indices before touching the DB. 0=Mon … 6=Sun.
    for d in body.days:
        if not isinstance(d, int) or d < 0 or d > 6:
            raise HTTPException(status_code=400, detail="days must be integers in [0, 6]")
    clean_days = sorted(set(body.days))
    db.query(AcademySchedule).update({"is_active": False})
    for day in clean_days:
        existing = db.query(AcademySchedule).filter(AcademySchedule.day_of_week == day).first()
        if existing:
            existing.is_active = True
            existing.memo = body.memo
        else:
            db.add(AcademySchedule(day_of_week=day, memo=body.memo, is_active=True))
    db.commit()
    return {"ok": True}


# ─── Config (PIN, email) ──────────────────────────────────────

# Whitelist of AppConfig keys safely readable via the public GET endpoint.
# Excludes "pin" so the PIN itself never leaks over the wire.
_READABLE_CONFIG_KEYS = {"parent_email"}


@router.get("/api/parent/config/{key}")
def parent_get_config(key: str, db: Session = Depends(get_db)):
    """Read a whitelisted AppConfig value. Returns "" if unset. @tag PARENT SETTINGS"""
    if key not in _READABLE_CONFIG_KEYS:
        raise HTTPException(status_code=404, detail="Config key not readable")
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return {"key": key, "value": (row.value or "") if row else ""}


# Pragmatic email regex: RFC 5322 is too permissive for a UI validator.
# This matches the HTML5 `email` input spec (WHATWG):
#   - local part: 1+ chars from a-z, A-Z, 0-9, and !#$%&'*+/=?^_`{|}~.-
#   - single @
#   - domain: DNS-style labels separated by dots, 1–63 chars each, no
#     leading/trailing hyphens, TLD at least 2 chars
# The old pattern `[^@\s]+@[^@\s]+\.[^@\s]+` accepted nonsense like
# `a@b.c` or `,,,@,,,.,,` — harmless in isolation but it means a typo'd
# parent_email never gets flagged and notifications silently never land.
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$"
)


@router.post("/api/parent/config")
def parent_set_config(
    body: ConfigIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Set an AppConfig key/value (e.g. PIN, parent_email). PIN-protected. @tag PARENT SETTINGS PIN"""
    if body.key == "pin":
        if not body.value.isdigit() or len(body.value) != 4:
            raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
        # Never persist the 4-digit PIN as plaintext — always hash before
        # writing. Verify path uses pin_hash.verify_pin() which handles both
        # formats, so legacy rows still work until they self-upgrade.
        stored_value = pin_hash.hash_pin(body.value)
    elif body.key == "parent_email":
        body.value = body.value.strip()
        if body.value and not _EMAIL_RE.match(body.value):
            raise HTTPException(status_code=400, detail="Invalid email address")
        stored_value = body.value
    else:
        stored_value = body.value
    row = db.query(AppConfig).filter(AppConfig.key == body.key).first()
    now = datetime.now().isoformat()
    if row:
        row.value = stored_value
        row.updated_at = now
    else:
        db.add(AppConfig(key=body.key, value=stored_value, updated_at=now))
    db.commit()
    return {"ok": True}


# ─── Shared helpers (used by parent_streak.py, parent_xp.py) ─────

def _upsert_app_config(db: Session, key: str, value: str, now: str) -> None:
    """Insert or update a single AppConfig row. Callers must db.commit()."""
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        row.value = value
        row.updated_at = now
    else:
        db.add(AppConfig(key=key, value=value, updated_at=now))


# ─── Day Off Requests ─────────────────────────────────────────

@router.get("/api/parent/day-off-requests")
def parent_day_off_list(db: Session = Depends(get_db)):
    """Return all day-off requests ordered by date DESC. @tag PARENT DAY_OFF"""
    rows = db.query(DayOffRequest).order_by(DayOffRequest.request_date.desc()).all()
    return {"requests": [
        {"id": r.id, "request_date": r.request_date, "reason": r.reason,
         "status": r.status, "parent_response": r.parent_response or ""}
        for r in rows
    ]}


@router.put("/api/parent/day-off-requests/{req_id}")
def parent_decide_day_off(
    req_id: int,
    body: DayOffDecisionIn,
    db: Session = Depends(get_db),
    _pin: bool = Depends(require_parent_pin),
):
    """Approve or deny a day-off request. PIN-protected. @tag PARENT DAY_OFF"""
    if body.status not in ("approved", "denied"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'denied'")
    row = db.query(DayOffRequest).filter(DayOffRequest.id == req_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    row.status = body.status
    row.parent_response = body.parent_response
    db.commit()
    return {"ok": True}
