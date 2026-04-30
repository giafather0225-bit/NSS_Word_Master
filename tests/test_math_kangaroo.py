"""Tests for backend/routers/math_kangaroo.py."""
import json
from pathlib import Path

import pytest

from backend.models import MathKangarooProgress, StreakLog, XPLog


_KANGAROO_DIR = Path(__file__).resolve().parents[1] / "backend" / "data" / "math" / "kangaroo"


def _pick_set_id() -> str:
    """Pick any available kangaroo set id for tests."""
    files = sorted(_KANGAROO_DIR.glob("*.json"))
    assert files, "no kangaroo sets found"
    return files[0].stem


def _first_question(set_id: str) -> dict:
    data = json.loads((_KANGAROO_DIR / f"{set_id}.json").read_text("utf-8"))
    for section in data.get("sections", []) or []:
        for q in section.get("questions", []) or []:
            return q
    raise AssertionError("set had no embedded questions (past paper / PDF-only)")


# Kangaroo migrated to PDF-based past papers (commit e1514a6 / migration 017+);
# embedded questions and per-question grading endpoints no longer feed off the
# JSON files. The 5 tests below assume the legacy schema and are skipped until
# rewritten against the past-paper flow (sections_meta + answer key + /submit).
_KANGAROO_LEGACY_SKIP = pytest.mark.skip(
    reason="kangaroo schema migrated to PDF-only past papers; "
           "needs rewrite against new sections_meta / answer-key flow"
)


@pytest.fixture(autouse=True)
def _clean_kangaroo_tables(db_session):
    models = (MathKangarooProgress, XPLog, StreakLog)
    for m in models:
        db_session.query(m).delete()
    db_session.commit()
    yield
    for m in models:
        db_session.query(m).delete()
    db_session.commit()


def test_list_sets(client):
    resp = client.get("/api/math/kangaroo/sets")
    assert resp.status_code == 200
    sets = resp.json()["sets"]
    assert len(sets) > 0
    s = sets[0]
    for field in ("set_id", "title", "level", "total_questions", "max_score", "category"):
        assert field in s
    # Fresh DB — nothing completed
    assert all(not s["completed"] for s in sets)
    assert all(s["best_score"] is None for s in sets)


@_KANGAROO_LEGACY_SKIP
def test_get_set_strips_answers(client):
    set_id = _pick_set_id()
    resp = client.get(f"/api/math/kangaroo/set/{set_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["set_id"] == set_id
    assert len(body["sections"]) > 0
    for section in body["sections"]:
        for q in section["questions"]:
            assert "answer" not in q
            assert "solution" not in q
            assert "id" in q


def test_get_set_not_found(client):
    resp = client.get("/api/math/kangaroo/set/does_not_exist_xyz")
    assert resp.status_code == 404


@_KANGAROO_LEGACY_SKIP
def test_submit_answer_correct(client):
    set_id = _pick_set_id()
    q = _first_question(set_id)
    resp = client.post(
        "/api/math/kangaroo/submit-answer",
        json={"set_id": set_id, "question_id": q["id"], "answer": q["answer"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["correct_answer"] == str(q["answer"]).upper()
    assert body["points_earned"] > 0


@_KANGAROO_LEGACY_SKIP
def test_submit_answer_wrong(client):
    set_id = _pick_set_id()
    q = _first_question(set_id)
    # Pick a guaranteed-wrong option letter
    wrong = "Z" if str(q["answer"]).upper() != "Z" else "Y"
    resp = client.post(
        "/api/math/kangaroo/submit-answer",
        json={"set_id": set_id, "question_id": q["id"], "answer": wrong},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is False
    assert body["points_earned"] == 0


@_KANGAROO_LEGACY_SKIP
def test_submit_answer_question_not_found(client):
    set_id = _pick_set_id()
    resp = client.post(
        "/api/math/kangaroo/submit-answer",
        json={"set_id": set_id, "question_id": "ghost_q", "answer": "A"},
    )
    assert resp.status_code == 404


@_KANGAROO_LEGACY_SKIP
def test_submit_full_set_awards_and_persists(client, db_session):
    set_id = _pick_set_id()
    data = json.loads((_KANGAROO_DIR / f"{set_id}.json").read_text("utf-8"))
    # Build perfect answer list
    answers = []
    for section in data["sections"]:
        for q in section["questions"]:
            answers.append({"question_id": q["id"], "answer": q["answer"]})

    resp = client.post(
        "/api/math/kangaroo/submit",
        json={"set_id": set_id, "answers": answers, "time_spent_seconds": 600},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["perfect"] is True
    assert body["percentage"] == 100.0
    assert body["is_new_best"] is True
    # 5 (complete) + 5 (≥80) + 10 (perfect) = 20
    assert body["xp_earned"] == 20

    row = db_session.query(MathKangarooProgress).filter_by(set_id=set_id).first()
    assert row is not None
    assert row.score == row.max_score
    assert row.completed_at is not None
