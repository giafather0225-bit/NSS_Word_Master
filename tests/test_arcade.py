"""Tests for backend/routers/arcade.py.

Covers the word-pool endpoint, personal-best read/write, and the score
submission flow — including the input validation guards and the atomic
XP + best-score commit path (commit=False bundling, see commit bc0d167).
"""

import pytest


# ── GET /api/arcade/words ─────────────────────────────────────────────

def test_words_empty_pool(client):
    """Empty DB → endpoint returns the documented shape, not a 500."""
    resp = client.get("/api/arcade/words")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("words", "source", "unique_count", "due_count"):
        assert key in body
    assert isinstance(body["words"], list)
    assert body["unique_count"] == 0


def test_words_count_clamped(client):
    """count is clamped to [10, 200]; out-of-range values must not error."""
    assert client.get("/api/arcade/words?count=1").status_code == 200
    assert client.get("/api/arcade/words?count=9999").status_code == 200


def test_words_with_seeded_pool(client, db_session):
    """Seeded Word rows show up in the pool."""
    from backend.models import Word
    db_session.add_all([
        Word(word="apple", definition="a round fruit"),
        Word(word="brisk", definition="quick and energetic"),
    ])
    db_session.commit()

    resp = client.get("/api/arcade/words")
    assert resp.status_code == 200
    body = resp.json()
    assert body["unique_count"] == 2
    words = {w["word"] for w in body["words"]}
    assert "apple" in words and "brisk" in words


# ── GET /api/arcade/best/{game} ───────────────────────────────────────

def test_best_unknown_game_422(client):
    resp = client.get("/api/arcade/best/not_a_real_game")
    assert resp.status_code == 422


def test_best_no_record_returns_zero(client):
    resp = client.get("/api/arcade/best/word_invaders")
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 0
    assert body["date"] == ""


# ── POST /api/arcade/score — validation ───────────────────────────────

def _score_body(**over):
    base = {
        "game": "word_invaders",
        "score": 600,
        "correct": 8,
        "total": 10,
        "accuracy": 0.8,
        "level": "",
    }
    base.update(over)
    return base


def test_score_unknown_game_422(client):
    resp = client.post("/api/arcade/score", json=_score_body(game="bogus"))
    assert resp.status_code == 422


def test_score_correct_exceeds_total_422(client):
    resp = client.post("/api/arcade/score", json=_score_body(correct=11, total=10))
    assert resp.status_code == 422


def test_score_accuracy_mismatch_422(client):
    """accuracy must match correct/total within 1% tolerance."""
    resp = client.post("/api/arcade/score", json=_score_body(correct=5, total=10, accuracy=0.95))
    assert resp.status_code == 422


def test_score_negative_score_422(client):
    """Pydantic ge=0 blocks negative score."""
    resp = client.post("/api/arcade/score", json=_score_body(score=-1))
    assert resp.status_code == 422


# ── POST /api/arcade/score — happy path ───────────────────────────────

def test_score_awards_xp_and_sets_best(client):
    """A 600-point round (tier 1) awards XP and records a new best.

    Uses a unique level so the best-score key is isolated from other tests
    (in-memory DB persists committed rows across the session via StaticPool).
    """
    resp = client.post("/api/arcade/score", json=_score_body(score=600, level="t_award"))
    assert resp.status_code == 200
    body = resp.json()
    for key in ("tier", "xp_awarded", "daily_total", "daily_cap",
                "best_score", "new_best", "prev_best"):
        assert key in body
    assert body["tier"] == 1
    assert body["new_best"] is True
    assert body["best_score"] == 600
    assert body["prev_best"] == 0


def test_score_lower_than_best_not_new_best(client):
    """Submitting a lower score after a high score does not overwrite best."""
    client.post("/api/arcade/score", json=_score_body(score=2000, level="t_lower"))
    resp = client.post("/api/arcade/score", json=_score_body(score=500, level="t_lower"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["new_best"] is False
    assert body["best_score"] == 2000
    assert body["prev_best"] == 2000


def test_score_best_persists_across_reads(client):
    """A best set via POST is visible via GET /best/{game}."""
    client.post("/api/arcade/score", json=_score_body(score=1500, level="t_persist"))
    resp = client.get("/api/arcade/best/word_invaders?level=t_persist")
    assert resp.status_code == 200
    assert resp.json()["score"] == 1500


def test_score_below_tier_threshold_zero_xp(client):
    """A sub-500 score is tier 0 → no XP, but still 200 OK."""
    resp = client.post("/api/arcade/score", json=_score_body(score=100, correct=1, total=10, accuracy=0.1))
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == 0
    assert body["xp_awarded"] == 0


def test_score_best_scoped_by_level(client):
    """Best scores are tracked independently per level."""
    client.post("/api/arcade/score", json=_score_body(score=800, level="easy"))
    client.post("/api/arcade/score", json=_score_body(score=1600, level="hard"))
    easy = client.get("/api/arcade/best/word_invaders?level=easy").json()
    hard = client.get("/api/arcade/best/word_invaders?level=hard").json()
    assert easy["score"] == 800
    assert hard["score"] == 1600
