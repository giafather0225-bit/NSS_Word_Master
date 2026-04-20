"""Tests for backend/routers/math_academy.py."""
import pytest

from backend.models import (
    AppConfig,
    MathAttempt,
    MathProgress,
    MathWrongReview,
    StreakLog,
    XPLog,
)
from backend.routers.math_academy import (
    _answers_equivalent,
    _normalize_math_answer,
)


@pytest.fixture(autouse=True)
def _clean_math_tables(db_session):
    """Endpoints commit to the shared in-memory DB; wipe tables each test."""
    models = (MathAttempt, MathProgress, MathWrongReview, XPLog, StreakLog, AppConfig)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


# ── GET endpoints ─────────────────────────────────────────────

def test_get_grades(client):
    resp = client.get("/api/math/academy/grades")
    assert resp.status_code == 200
    grades = resp.json()["grades"]
    for g in ("G3", "G4", "G5", "G6"):
        assert g in grades


def test_get_units(client):
    resp = client.get("/api/math/academy/G3/units")
    assert resp.status_code == 200
    body = resp.json()
    assert body["grade"] == "G3"
    assert len(body["units"]) > 0
    assert "U1_add_sub_1000" in body["units"]


def test_get_lessons(client):
    resp = client.get("/api/math/academy/G3/U1_add_sub_1000/lessons")
    assert resp.status_code == 200
    body = resp.json()
    assert body["grade"] == "G3"
    assert body["unit"] == "U1_add_sub_1000"
    assert len(body["lessons"]) > 0
    for item in body["lessons"]:
        assert "name" in item
        assert "is_completed" in item
        assert "stage" in item
        assert item["is_completed"] is False  # clean DB


def test_get_stage_problems(client):
    resp = client.get(
        "/api/math/academy/G3/U1_add_sub_1000/L1_number_patterns/pretest"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stage"] == "pretest"
    assert body["count"] > 0
    assert len(body["problems"]) == body["count"]
    first = body["problems"][0]
    assert "id" in first


def test_get_stage_invalid(client):
    resp = client.get(
        "/api/math/academy/G3/U1_add_sub_1000/L1_number_patterns/invalid_stage"
    )
    assert resp.status_code == 400


def test_get_unit_test(client):
    resp = client.get("/api/math/academy/G3/U1_add_sub_1000/unit-test")
    assert resp.status_code == 200
    body = resp.json()
    assert "problems" in body
    assert isinstance(body["problems"], list)


def test_get_unit_test_404(client):
    resp = client.get("/api/math/academy/G3/U99_nonexistent/unit-test")
    assert resp.status_code == 404


# ── Submit answer ─────────────────────────────────────────────

def _submit(client, user_answer: str, problem_id: str = "PT_01"):
    return client.post(
        "/api/math/academy/submit-answer",
        json={
            "problem_id": problem_id,
            "grade": "G3",
            "unit": "U1_add_sub_1000",
            "lesson": "L1_number_patterns",
            "stage": "pretest",
            "user_answer": user_answer,
            "time_spent_sec": 5,
        },
    )


def test_submit_answer_correct(client):
    # PT_01 correct_answer = "B"
    resp = _submit(client, "B")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["correct_answer"] == "B"


def test_submit_answer_wrong(client):
    resp = _submit(client, "A")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is False
    assert body["correct_answer"] == "B"


def test_submit_answer_not_found(client):
    resp = _submit(client, "B", problem_id="PT_NOT_REAL")
    assert resp.status_code == 404


# ── Phase-0 endpoints ─────────────────────────────────────────

def test_complete_lesson(client):
    resp = client.post(
        "/api/math/academy/complete-lesson",
        json={"grade": "G3", "unit": "U1_add_sub_1000", "lesson": "L1_number_patterns"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["is_completed"] is True


def test_complete_lesson_progress_saved(client):
    client.post(
        "/api/math/academy/complete-lesson",
        json={"grade": "G3", "unit": "U1_add_sub_1000", "lesson": "L1_number_patterns"},
    )
    resp = client.get("/api/math/academy/G3/U1_add_sub_1000/lessons")
    assert resp.status_code == 200
    lessons = resp.json()["lessons"]
    target = next(l for l in lessons if l["name"] == "L1_number_patterns")
    assert target["is_completed"] is True


def test_unit_test_submit_v2_pass(client):
    resp = client.post(
        "/api/math/academy/unit-test/submit-v2",
        json={"grade": "G3", "unit": "U1_add_sub_1000", "score": 8, "total": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is True
    assert body["score"] == 8
    assert body["total"] == 10


def test_unit_test_submit_v2_fail(client):
    # Record a wrong attempt to drive weak_lesson selection
    client.post(
        "/api/math/academy/submit-answer",
        json={
            "problem_id": "PT_01",
            "grade": "G3",
            "unit": "U1_add_sub_1000",
            "lesson": "L1_number_patterns",
            "stage": "learn",
            "user_answer": "A",
            "time_spent_sec": 3,
        },
    )
    resp = client.post(
        "/api/math/academy/unit-test/submit-v2",
        json={"grade": "G3", "unit": "U1_add_sub_1000", "score": 5, "total": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is False
    # weak_lesson is optional (depends on recorded MathAttempts in-unit)
    if "weak_lesson" in body:
        assert body["weak_lesson"] == "L1_number_patterns"


# ── Helper unit tests ─────────────────────────────────────────

def test_normalize_math_answer():
    assert _normalize_math_answer("  42  ") == "42"
    assert _normalize_math_answer("1,234") == "1234"
    assert _normalize_math_answer("$50") == "50"
    assert _normalize_math_answer("25%") == "25"
    assert _normalize_math_answer("ABC") == "abc"
    assert _normalize_math_answer("a   b") == "a b"
    assert _normalize_math_answer("") == ""
    assert _normalize_math_answer(None) == ""  # type: ignore[arg-type]


def test_answers_equivalent_numeric():
    assert _answers_equivalent("1/2", "0.5") is True
    assert _answers_equivalent("0.5", "1/2") is True
    assert _answers_equivalent("3/4", "0.75") is True
    assert _answers_equivalent("1,000", "1000") is True
    assert _answers_equivalent("$50", "50") is True
    assert _answers_equivalent("1/2", "0.6") is False


def test_answers_equivalent_string():
    assert _answers_equivalent("Apple", "apple") is True
    assert _answers_equivalent("  YES  ", "yes") is True
    assert _answers_equivalent("true", "TRUE") is True
    assert _answers_equivalent("cat", "dog") is False
