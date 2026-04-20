"""Tests for backend/routers/math_placement.py."""
import pytest

from backend.models import MathPlacementResult


@pytest.fixture(autouse=True)
def _clean_placement_tables(db_session):
    db_session.query(MathPlacementResult).delete()
    db_session.commit()
    yield
    db_session.query(MathPlacementResult).delete()
    db_session.commit()


def test_status_empty_initially(client):
    resp = client.get("/api/math/placement/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["taken"] is False
    assert body["domains_tested"] == 0


def test_start_returns_domains_without_answers(client):
    resp = client.get("/api/math/placement/start")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] >= 1
    domain_keys = {d["domain"] for d in body["domains"]}
    for expected in ("number_operations", "measurement_data", "geometry", "algebraic_thinking"):
        assert expected in domain_keys
    # Answers must be stripped
    for d in body["domains"]:
        for q in d["questions"]:
            assert "answer" not in q
            assert "id" in q and "grade" in q and "question" in q


def test_results_empty_returns_404(client):
    resp = client.get("/api/math/placement/results")
    assert resp.status_code == 404


def test_save_scores_and_persists(client, db_session):
    # Correct answers to number_operations G2 → should estimate G2+
    payload = {
        "results": [
            {
                "domain": "number_operations",
                "answers": {"no_g2_1": "72", "no_g2_2": "44"},
            }
        ]
    }
    resp = client.post("/api/math/placement/save", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "number_operations" in body["saved_domains"]
    assert body["suggested_grade"] in ("G2", "G3", "G4", "G5", "G6")
    assert len(body["results"]) == 1
    assert body["results"][0]["raw_score"] >= 2
    # Persistence
    rows = db_session.query(MathPlacementResult).all()
    assert len(rows) == 1


def test_status_after_save(client):
    client.post(
        "/api/math/placement/save",
        json={"results": [{"domain": "number_operations", "answers": {}}]},
    )
    status = client.get("/api/math/placement/status").json()
    assert status["taken"] is True
    assert status["domains_tested"] == 1


def test_adaptive_next_unknown_domain(client):
    resp = client.post(
        "/api/math/placement/next",
        json={"domain": "bogus", "history": []},
    )
    assert resp.status_code == 404


def test_adaptive_next_returns_question(client):
    resp = client.post(
        "/api/math/placement/next",
        json={"domain": "number_operations", "history": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["done"] is False
    assert body["target_grade"] == "G3"
    assert "answer" not in body["question"]
    assert "id" in body["question"]


def test_adaptive_check_grades_answer(client):
    # no_g2_1 answer is "72"
    resp = client.post(
        "/api/math/placement/check",
        json={"domain": "number_operations", "question_id": "no_g2_1", "answer": "72"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_correct"] is True
    assert body["grade"] == "G2"
