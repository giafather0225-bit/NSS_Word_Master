"""Tests for routers/parent.py — Parent Dashboard core: PIN, task settings,
academy schedule, config, day-off decisions.

PIN: no `pin` AppConfig row → DEFAULT_PIN "0000". Mutation endpoints require
the X-Parent-Pin header. The autouse fixture wipes AppConfig (which also
holds pin_guard rate-limit state) so lockout never leaks across tests.
"""
import pytest

from backend.models import AppConfig, TaskSetting, AcademySchedule, DayOffRequest

PIN = {"X-Parent-Pin": "0000"}


@pytest.fixture(autouse=True)
def _clean_tables(db_session):
    def _wipe():
        for model in (AppConfig, TaskSetting, AcademySchedule, DayOffRequest):
            db_session.query(model).delete()
        db_session.commit()
    _wipe()
    yield
    _wipe()


# ── PIN verification ──────────────────────────────────────────

def test_verify_pin_correct(client):
    r = client.post("/api/parent/verify-pin", json={"pin": "0000"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_verify_pin_wrong(client):
    assert client.post("/api/parent/verify-pin",
                       json={"pin": "9999"}).status_code == 403


# ── Task Settings ─────────────────────────────────────────────

def test_task_settings_get_empty(client):
    assert client.get("/api/parent/task-settings").json() == {"tasks": []}


def test_update_task_requires_pin(client, db_session):
    db_session.add(TaskSetting(task_key="journal", is_required=True, xp_value=10))
    db_session.commit()
    r = client.put("/api/parent/task-settings/journal", json={"xp_value": 20})
    assert r.status_code == 403


def test_update_task_404(client):
    r = client.put("/api/parent/task-settings/nope",
                   json={"xp_value": 20}, headers=PIN)
    assert r.status_code == 404


def test_update_task_success(client, db_session):
    db_session.add(TaskSetting(task_key="journal", is_required=True, xp_value=10))
    db_session.commit()
    r = client.put("/api/parent/task-settings/journal",
                   json={"xp_value": 25, "is_required": False}, headers=PIN)
    assert r.status_code == 200
    db_session.expire_all()
    row = db_session.query(TaskSetting).filter_by(task_key="journal").first()
    assert row.xp_value == 25
    assert row.is_required is False


# ── Academy Schedule ──────────────────────────────────────────

def test_schedule_get_empty(client):
    assert client.get("/api/parent/academy-schedule").json() == {"days": []}


def test_set_schedule_requires_pin(client):
    assert client.post("/api/parent/academy-schedule",
                       json={"days": [0, 1]}).status_code == 403


def test_set_schedule_success(client):
    r = client.post("/api/parent/academy-schedule",
                    json={"days": [0, 2], "memo": "test days"}, headers=PIN)
    assert r.status_code == 200
    days = client.get("/api/parent/academy-schedule").json()["days"]
    assert sorted(d["day_of_week"] for d in days) == [0, 2]


def test_set_schedule_invalid_day_400(client):
    r = client.post("/api/parent/academy-schedule",
                    json={"days": [99]}, headers=PIN)
    assert r.status_code == 400


# ── Config ────────────────────────────────────────────────────

def test_get_config_not_readable_404(client):
    # "pin" is excluded from the readable whitelist.
    assert client.get("/api/parent/config/pin").status_code == 404


def test_get_config_readable_unset(client):
    body = client.get("/api/parent/config/parent_email").json()
    assert body == {"key": "parent_email", "value": ""}


def test_set_config_requires_pin(client):
    r = client.post("/api/parent/config",
                    json={"key": "parent_email", "value": "a@b.com"})
    assert r.status_code == 403


def test_set_config_pin_must_be_4_digits(client):
    r = client.post("/api/parent/config",
                    json={"key": "pin", "value": "12"}, headers=PIN)
    assert r.status_code == 400


def test_set_config_invalid_email_400(client):
    r = client.post("/api/parent/config",
                    json={"key": "parent_email", "value": "notanemail"},
                    headers=PIN)
    assert r.status_code == 400


def test_set_config_valid_email(client):
    r = client.post("/api/parent/config",
                    json={"key": "parent_email", "value": "mom@example.com"},
                    headers=PIN)
    assert r.status_code == 200
    assert client.get("/api/parent/config/parent_email").json()["value"] == \
        "mom@example.com"


# ── Day Off Requests ──────────────────────────────────────────

def test_day_off_list_empty(client):
    assert client.get("/api/parent/day-off-requests").json() == {"requests": []}


def test_decide_day_off_requires_pin(client, db_session):
    db_session.add(DayOffRequest(request_date="2026-05-15", reason="sick",
                                 status="pending"))
    db_session.commit()
    r = client.put("/api/parent/day-off-requests/1",
                   json={"status": "approved"})
    assert r.status_code == 403


def test_decide_day_off_404(client):
    r = client.put("/api/parent/day-off-requests/9999",
                   json={"status": "approved"}, headers=PIN)
    assert r.status_code == 404


def test_decide_day_off_invalid_status_400(client, db_session):
    db_session.add(DayOffRequest(request_date="2026-05-15", reason="sick",
                                 status="pending"))
    db_session.commit()
    r = client.put("/api/parent/day-off-requests/1",
                   json={"status": "maybe"}, headers=PIN)
    assert r.status_code == 400


def test_decide_day_off_success(client, db_session):
    db_session.add(DayOffRequest(request_date="2026-05-15", reason="sick",
                                 status="pending"))
    db_session.commit()
    r = client.put("/api/parent/day-off-requests/1",
                   json={"status": "approved", "parent_response": "Get well"},
                   headers=PIN)
    assert r.status_code == 200
    db_session.expire_all()
    row = db_session.query(DayOffRequest).first()
    assert row.status == "approved"
    assert row.parent_response == "Get well"
