"""Tests for backend/routers/parent_xp.py — parent XP rules + report.

Covers the read-only xp-rules and xp-report endpoints plus the two
PIN-gated mutations (rule save with validation, rule reset). PIN falls
back to DEFAULT_PIN "0000" on the test host.
"""

from datetime import date, datetime, timedelta

import pytest

_PIN_HEADER = {"X-Parent-Pin": "0000"}


@pytest.fixture(autouse=True)
def _clean_xp_tables(db_session):
    """Wipe XPLog + xp_rule_* / arcade_daily_cap / pin AppConfig rows.

    Also invalidates the xp_engine TTL cache so a previous test's saved
    rule override can't bleed into the next via the 30-second cache.
    """
    from backend.models import XPLog, AppConfig
    from backend.services import xp_engine
    def _wipe():
        xp_engine.invalidate_xp_cache()
        db_session.query(XPLog).delete()
        db_session.query(AppConfig).filter(
            (AppConfig.key.like("xp_rule_%")) |
            (AppConfig.key == "arcade_daily_cap") |
            (AppConfig.key == "pin")
        ).delete(synchronize_session=False)
        db_session.commit()
    _wipe()
    yield
    _wipe()


# ── GET /api/parent/xp-rules ──────────────────────────────────────────

def test_xp_rules_shape(client):
    resp = client.get("/api/parent/xp-rules")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("rules", "defaults", "arcade_daily_cap", "arcade_cap_default"):
        assert key in body
    # Defaults match the engine's XP_RULES_DEFAULT
    from backend.services import xp_engine
    assert body["defaults"] == dict(xp_engine.XP_RULES_DEFAULT)


# ── POST /api/parent/xp-rules ─────────────────────────────────────────

def test_xp_rules_save_no_pin_403(client):
    resp = client.post("/api/parent/xp-rules",
                       json={"rules": {"word_correct": 3}})
    assert resp.status_code == 403


def test_xp_rules_save_unknown_action_400(client):
    resp = client.post("/api/parent/xp-rules",
                       json={"rules": {"not_a_real_action": 5}},
                       headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_xp_rules_save_invalid_value_400(client):
    resp = client.post("/api/parent/xp-rules",
                       json={"rules": {"word_correct": 99999}},
                       headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_xp_rules_save_bad_arcade_cap_400(client):
    resp = client.post("/api/parent/xp-rules",
                       json={"arcade_daily_cap": 99999},
                       headers=_PIN_HEADER)
    assert resp.status_code == 400


def test_xp_rules_save_success(client):
    resp = client.post("/api/parent/xp-rules",
                       json={"rules": {"word_correct": 3}, "arcade_daily_cap": 20},
                       headers=_PIN_HEADER)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    # Reflected in the GET payload
    rules = client.get("/api/parent/xp-rules").json()
    assert rules["rules"]["word_correct"] == 3
    assert rules["arcade_daily_cap"] == 20


# ── POST /api/parent/xp-rules/reset ───────────────────────────────────

def test_xp_rules_reset_no_pin_403(client):
    resp = client.post("/api/parent/xp-rules/reset")
    assert resp.status_code == 403


def test_xp_rules_reset_restores_defaults(client):
    # Override, then reset
    client.post("/api/parent/xp-rules",
                json={"rules": {"word_correct": 9}}, headers=_PIN_HEADER)
    reset = client.post("/api/parent/xp-rules/reset", headers=_PIN_HEADER)
    assert reset.status_code == 200
    from backend.services import xp_engine
    rules = client.get("/api/parent/xp-rules").json()["rules"]
    assert rules["word_correct"] == xp_engine.XP_RULES_DEFAULT["word_correct"]


# ── GET /api/parent/xp-report ─────────────────────────────────────────

def test_xp_report_default_7_days(client):
    resp = client.get("/api/parent/xp-report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["days"] == 7
    assert len(body["daily"]) == 7
    assert body["total_xp"] == 0
    assert body["by_action"] == []


def test_xp_report_days_out_of_range_422(client):
    assert client.get("/api/parent/xp-report?days=0").status_code == 422
    assert client.get("/api/parent/xp-report?days=999").status_code == 422


def test_xp_report_reflects_seeded_xp(client, db_session):
    from backend.models import XPLog
    db_session.add(XPLog(action="stage_complete", xp_amount=25, detail="",
                         earned_date=date.today().isoformat(),
                         created_at=datetime.now().isoformat()))
    db_session.commit()
    body = client.get("/api/parent/xp-report?days=1").json()
    assert body["total_xp"] >= 25
    assert body["daily"][0]["xp"] >= 25
    actions = {r["action"] for r in body["by_action"]}
    assert "stage_complete" in actions
