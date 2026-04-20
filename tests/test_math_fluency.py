"""Tests for backend/routers/math_fluency.py."""
import pytest

from backend.models import MathFactFluency, StreakLog, XPLog


@pytest.fixture(autouse=True)
def _clean_fluency_tables(db_session):
    models = (MathFactFluency, XPLog, StreakLog)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


def test_catalog_lists_all_fact_sets(client):
    resp = client.get("/api/math/fluency/catalog")
    assert resp.status_code == 200
    sets = resp.json()["fact_sets"]
    keys = {s["fact_set"] for s in sets}
    for expected in ("add_within_10", "sub_within_10", "mul_0_5", "div_0_10"):
        assert expected in keys
    # Defaults for untouched sets
    first = sets[0]
    assert first["current_phase"] == "A"
    assert first["best_score"] == 0


def test_start_round_unknown_fact_set(client):
    resp = client.get("/api/math/fluency/start-round", params={"fact_set": "nope"})
    assert resp.status_code == 404


def test_start_round_returns_questions(client):
    resp = client.get(
        "/api/math/fluency/start-round",
        params={"fact_set": "add_within_10", "count": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["fact_set"] == "add_within_10"
    assert body["op"] == "+"
    assert body["phase"] == "A"
    assert len(body["questions"]) > 0
    assert all("question" in q and "answer" in q for q in body["questions"])


def test_start_round_clamps_count(client):
    # Count 3 should be clamped up to minimum 5
    resp = client.get(
        "/api/math/fluency/start-round",
        params={"fact_set": "add_within_10", "count": 3},
    )
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) >= 5


def test_submit_round_creates_progress(client, db_session):
    resp = client.post(
        "/api/math/fluency/submit-round",
        json={"fact_set": "add_within_10", "score": 8, "total": 10, "time_sec": 45},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["accuracy"] == 80.0
    assert body["current_phase"] == "A"
    assert body["total_rounds"] == 1
    row = db_session.query(MathFactFluency).filter_by(fact_set="add_within_10").first()
    assert row is not None
    assert row.best_score == 8


def test_submit_perfect_round_advances_phase(client):
    # First submission creates row with total_rounds=1 (phase stays "A")
    client.post(
        "/api/math/fluency/submit-round",
        json={"fact_set": "add_within_10", "score": 5, "total": 10, "time_sec": 30},
    )
    # Second submission: perfect round bumps A→B
    resp = client.post(
        "/api/math/fluency/submit-round",
        json={"fact_set": "add_within_10", "score": 10, "total": 10, "time_sec": 25},
    )
    assert resp.status_code == 200
    assert resp.json()["current_phase"] == "B"


def test_status_and_summary(client):
    client.post(
        "/api/math/fluency/submit-round",
        json={"fact_set": "add_within_10", "score": 5, "total": 10, "time_sec": 30},
    )
    status = client.get("/api/math/fluency/status").json()
    assert len(status["fact_sets"]) == 1

    summary = client.get("/api/math/fluency/summary").json()
    assert summary["total_sets"] == 1
    assert summary["daily_target"] == 3
