"""
services/pin_guard.py — PIN attempt rate limiting (shared by parent + shop).
Section: System / Security
Dependencies: models.py (AppConfig)
API: called by routers/parent.py, routers/reward_shop.py

A 4-digit PIN has only 10,000 possible values. Without throttling, an
attacker (or a curious child in the browser console) could brute-force the
parent PIN in seconds. This module keeps a single-row counter per scope
in AppConfig and rejects with HTTP 429 once the threshold is hit.

Design:
  - Scope = "parent" or "shop" — separate buckets so one doesn't block the
    other.
  - State is stored as JSON in AppConfig under key `pin_attempts_<scope>`.
  - On failure: increment counter + stamp first_attempt_at.
  - On success: clear counter.
  - After LOCKOUT_SECONDS, the window resets even without success.

Limits (deliberately lenient for a family app):
  - MAX_ATTEMPTS = 5 failures
  - LOCKOUT_SECONDS = 300s (5 min)
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

try:
    from ..models import AppConfig
except ImportError:
    from models import AppConfig

MAX_ATTEMPTS     = 5
LOCKOUT_SECONDS  = 300


def _key(scope: str) -> str:
    return f"pin_attempts_{scope}"


def _load(db: Session, scope: str) -> dict:
    row = db.query(AppConfig).filter(AppConfig.key == _key(scope)).first()
    if not row or not row.value:
        return {"count": 0, "first_at": None}
    try:
        data = json.loads(row.value)
        if not isinstance(data, dict):
            return {"count": 0, "first_at": None}
        return {"count": int(data.get("count", 0)), "first_at": data.get("first_at")}
    except (ValueError, TypeError):
        return {"count": 0, "first_at": None}


def _save(db: Session, scope: str, state: dict) -> None:
    now_iso = datetime.now().isoformat()
    payload = json.dumps(state, ensure_ascii=False)
    row = db.query(AppConfig).filter(AppConfig.key == _key(scope)).first()
    if row:
        row.value = payload
        row.updated_at = now_iso
    else:
        db.add(AppConfig(key=_key(scope), value=payload, updated_at=now_iso))
    db.commit()


def _window_expired(first_at: str | None) -> bool:
    if not first_at:
        return True
    try:
        first = datetime.fromisoformat(first_at)
    except ValueError:
        return True
    return (datetime.now() - first).total_seconds() >= LOCKOUT_SECONDS


# @tag PIN @tag SECURITY
def assert_not_locked(db: Session, scope: str) -> None:
    """
    Raise HTTP 429 if the scope is currently locked out. Called *before*
    checking the PIN so attackers don't learn timing information.
    """
    state = _load(db, scope)
    if state["count"] >= MAX_ATTEMPTS and not _window_expired(state["first_at"]):
        raise HTTPException(
            status_code=429,
            detail=f"Too many wrong PIN attempts. Try again in {LOCKOUT_SECONDS // 60} minutes.",
        )


# @tag PIN @tag SECURITY
def record_failure(db: Session, scope: str) -> None:
    """Increment the failure counter, starting a new window if needed."""
    state = _load(db, scope)
    if _window_expired(state["first_at"]):
        state = {"count": 1, "first_at": datetime.now().isoformat()}
    else:
        state["count"] = int(state["count"]) + 1
    _save(db, scope, state)


# @tag PIN @tag SECURITY
def record_success(db: Session, scope: str) -> None:
    """Clear the failure counter on a correct PIN."""
    _save(db, scope, {"count": 0, "first_at": None})
