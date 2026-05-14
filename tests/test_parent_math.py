"""Tests for backend/routers/parent_math.py — parent dashboard math summary.

Single read-only aggregate endpoint. Tests verify the documented shape
on an empty DB and that seeded MathProgress / MathAttempt rows are
reflected in the academy + recent-7d aggregates.
"""

from datetime import date, datetime

import pytest


@pytest.fixture(autouse=True)
def _clean_math_tables(db_session):
    """Wipe math tables before/after each test (StaticPool persistence)."""
    from backend.models import (MathProgress, MathAttempt, MathWrongReview,
                                MathFactFluency, MathDailyChallenge,
                                MathKangarooProgress)
    from backend.models.math import MathSpacedReview, MathUnitTest
    models = (MathProgress, MathAttempt, MathWrongReview, MathFactFluency,
              MathDailyChallenge, MathKangarooProgress, MathSpacedReview,
              MathUnitTest)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


# ── GET /api/parent/math-summary ──────────────────────────────────────

def test_math_summary_empty_shape(client):
    resp = client.get("/api/parent/math-summary")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("academy", "recent_7d", "weak_areas", "wrong_review",
                "fluency", "daily_recent", "kangaroo", "spaced_review",
                "exit_quiz_history", "unit_test_history"):
        assert key in body
    assert body["academy"]["total_lessons"] == 0
    assert body["academy"]["completed"] == 0
    assert body["recent_7d"]["total_attempts"] == 0
    assert body["weak_areas"] == []
    assert body["wrong_review"] == {"pending": 0, "mastered": 0}


def test_math_summary_academy_counts(client, db_session):
    """Seeded MathProgress rows feed the academy counters."""
    from backend.models import MathProgress
    db_session.add_all([
        MathProgress(grade="G3", unit="U1", lesson="L1",
                     is_completed=True, exit_quiz_passed=True),
        MathProgress(grade="G3", unit="U1", lesson="L2",
                     is_completed=False, exit_quiz_passed=False),
    ])
    db_session.commit()
    body = client.get("/api/parent/math-summary").json()
    assert body["academy"]["total_lessons"] == 2
    assert body["academy"]["completed"] == 1
    assert body["academy"]["exit_quiz_passed"] == 1


def test_math_summary_recent_attempts_accuracy(client, db_session):
    """Recent MathAttempt rows feed the 7-day accuracy aggregate."""
    from backend.models import MathAttempt
    today = date.today().isoformat()
    db_session.add_all([
        MathAttempt(problem_id="p1", grade="G3", unit="U1", lesson="L1",
                    stage="try", user_answer="4", is_correct=True,
                    attempted_at=today),
        MathAttempt(problem_id="p2", grade="G3", unit="U1", lesson="L1",
                    stage="try", user_answer="9", is_correct=False,
                    attempted_at=today),
    ])
    db_session.commit()
    body = client.get("/api/parent/math-summary").json()
    assert body["recent_7d"]["total_attempts"] == 2
    assert body["recent_7d"]["correct_attempts"] == 1
    assert body["recent_7d"]["accuracy_pct"] == 50.0


def test_math_summary_weak_areas_from_wrong_attempts(client, db_session):
    """Wrong MathAttempt rows surface in weak_areas grouped by lesson."""
    from backend.models import MathAttempt
    today = date.today().isoformat()
    for i in range(3):
        db_session.add(MathAttempt(
            problem_id=f"w{i}", grade="G3", unit="U2", lesson="L_hard",
            stage="try", user_answer="x", is_correct=False, attempted_at=today,
        ))
    db_session.commit()
    body = client.get("/api/parent/math-summary").json()
    weak = {w["lesson"]: w["wrong_count"] for w in body["weak_areas"]}
    assert weak.get("L_hard") == 3
