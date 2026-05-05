"""Tests for backend/routers/math_problems.py (My Problems / wrong review)."""
from datetime import datetime, timedelta

import pytest

from backend.models import MathAttempt, MathWrongReview


# A real problem present in backend/data/math/ (chosen by inspection):
# G3/U1_add_sub_1000/L10_use_place_value_to_subtract → practice_r1[0] id=R1_01, answer=B.
_GRADE = "G3"
_UNIT = "U1_add_sub_1000"
_LESSON = "L10_use_place_value_to_subtract"
_PROBLEM_ID = "R1_01"
_CORRECT = "B"


@pytest.fixture(autouse=True)
def _clean_problem_tables(db_session):
    models = (MathWrongReview, MathAttempt)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


def _seed_wrong_review(db_session, *, due_today=True, is_mastered=False):
    """Create a MathAttempt + MathWrongReview pair pointing to a real problem."""
    attempt = MathAttempt(
        problem_id=_PROBLEM_ID,
        grade=_GRADE,
        unit=_UNIT,
        lesson=_LESSON,
        stage="practice_r1",
        is_correct=False,
        user_answer="A",
        error_type="concept_gap",
        time_spent_sec=5,
        attempted_at=datetime.now().isoformat(),
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    when = datetime.now() if due_today else (datetime.now() + timedelta(days=5))
    review = MathWrongReview(
        problem_id=_PROBLEM_ID,
        original_attempt_id=attempt.id,
        next_review_date=when.strftime("%Y-%m-%d"),
        interval_days=1,
        times_reviewed=0,
        is_mastered=is_mastered,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return attempt, review


def test_summary_empty(client):
    resp = client.get("/api/math/my-problems/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"total_pending": 0, "due_today": 0, "mastered": 0}


def test_summary_counts(client, db_session):
    _seed_wrong_review(db_session, due_today=True)
    _seed_wrong_review(db_session, due_today=False)
    # Mark one as mastered
    _, r3 = _seed_wrong_review(db_session, due_today=True)
    r3.is_mastered = True
    db_session.commit()

    resp = client.get("/api/math/my-problems/summary")
    body = resp.json()
    assert body["total_pending"] == 2
    assert body["due_today"] == 1
    assert body["mastered"] == 1


def test_review_empty(client):
    resp = client.get("/api/math/my-problems/review")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "count": 0}


def test_review_returns_due_items(client, db_session):
    _seed_wrong_review(db_session, due_today=True)
    resp = client.get("/api/math/my-problems/review")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    item = body["items"][0]
    assert item["problem_id"] == _PROBLEM_ID
    assert item["grade"] == _GRADE
    assert item["unit"] == _UNIT
    assert item["lesson"] == _LESSON
    assert item["problem"]["id"] == _PROBLEM_ID


def test_review_skips_future_items(client, db_session):
    _seed_wrong_review(db_session, due_today=False)
    resp = client.get("/api/math/my-problems/review")
    assert resp.json()["count"] == 0


def test_submit_correct_marks_mastered(client, db_session):
    """Two consecutive correct answers required for mastery."""
    _, review = _seed_wrong_review(db_session, due_today=True)

    # First correct — not yet mastered
    resp1 = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": review.id, "user_answer": _CORRECT},
    )
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["is_correct"] is True
    assert body1["is_mastered"] is False
    assert body1["consecutive_correct"] == 1
    assert body1["next_review_date"] is not None

    # Second correct — mastered
    resp2 = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": review.id, "user_answer": _CORRECT},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["is_correct"] is True
    assert body2["is_mastered"] is True
    assert body2["next_review_date"] is None
    db_session.refresh(review)
    assert review.is_mastered is True
    assert review.times_reviewed == 2


def test_submit_wrong_reschedules(client, db_session):
    _, review = _seed_wrong_review(db_session, due_today=True)
    resp = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": review.id, "user_answer": "definitely_wrong"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is False
    assert body["is_mastered"] is False
    assert body["next_review_date"] is not None
    db_session.refresh(review)
    assert review.is_mastered is False
    assert review.interval_days > 1  # interval advanced


def test_miss_penalty_1day_overdue(client, db_session):
    """1 day overdue: interval × 0.7, consecutive_correct reset."""
    attempt = MathAttempt(
        problem_id=_PROBLEM_ID, grade=_GRADE, unit=_UNIT, lesson=_LESSON,
        stage="practice_r1", is_correct=False, user_answer="A",
        error_type="concept_gap", time_spent_sec=5,
        attempted_at=datetime.now().isoformat(),
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    review = MathWrongReview(
        problem_id=_PROBLEM_ID, original_attempt_id=attempt.id,
        next_review_date=yesterday, interval_days=7,
        times_reviewed=1, is_mastered=False, consecutive_correct=1,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    resp = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": review.id, "user_answer": _CORRECT},
    )
    body = resp.json()
    assert body["is_correct"] is True
    # consecutive_correct was reset to 0 by miss penalty, then +1 for correct = 1
    assert body["consecutive_correct"] == 1
    assert body["is_mastered"] is False


def test_miss_penalty_2days_overdue_resets_interval(client, db_session):
    """2+ days overdue: interval reset to first (_INTERVALS[0] = 1 day)."""
    attempt = MathAttempt(
        problem_id=_PROBLEM_ID, grade=_GRADE, unit=_UNIT, lesson=_LESSON,
        stage="practice_r1", is_correct=False, user_answer="A",
        error_type="concept_gap", time_spent_sec=5,
        attempted_at=datetime.now().isoformat(),
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    review = MathWrongReview(
        problem_id=_PROBLEM_ID, original_attempt_id=attempt.id,
        next_review_date=three_days_ago, interval_days=21,
        times_reviewed=3, is_mastered=False, consecutive_correct=1,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)

    resp = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": review.id, "user_answer": _CORRECT},
    )
    body = resp.json()
    assert body["is_correct"] is True
    assert body["consecutive_correct"] == 1
    assert body["is_mastered"] is False
    db_session.refresh(review)
    assert review.interval_days == 1  # reset to first interval


def test_submit_unknown_review_id(client):
    resp = client.post(
        "/api/math/my-problems/submit-answer",
        json={"review_id": 99999, "user_answer": "A"},
    )
    assert resp.status_code == 200
    assert "error" in resp.json()
