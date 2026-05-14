"""Tests for backend/routers/review.py — SM-2 spaced repetition queue.

Covers lesson/word registration, the due-today queue, SM-2 result
submission and rescheduling, and the stats endpoint. Uses seeded
StudyItem + WordReview rows against the in-memory DB.

Note: review.py is a DUX-protected file (CLAUDE.md rule 14) — these
tests are additive and never modify the router itself.
"""

from datetime import date, timedelta


# ── Fixtures (local) ──────────────────────────────────────────────────

def _seed_study_items(db, subject="English", textbook="Voca_8000",
                      lesson="Lesson_01", n=3):
    """Insert n StudyItem rows for a lesson; return the list."""
    from backend.models import StudyItem
    items = [
        StudyItem(
            subject=subject, textbook=textbook, lesson=lesson,
            source_type="manual",
            question=f"definition {i}", answer=f"word{i}",
            hint=f"example {i}",
        )
        for i in range(n)
    ]
    db.add_all(items)
    db.commit()
    return items


def _seed_word_review(db, word="apple", next_review=None, **over):
    """Insert a single WordReview row, return it.

    `over` may override any column default (e.g. repetitions, interval,
    total_reviews) — it is merged last so callers win over the defaults.
    """
    from backend.models import WordReview
    if next_review is None:
        next_review = date.today().isoformat()
    fields = dict(
        study_item_id=None,
        word=word, subject="English", textbook="", lesson="",
        easiness="2.5", interval=0, repetitions=0,
        next_review=next_review, last_review="",
        total_reviews=0, total_correct=0,
        source="daily", question="a fruit", hint="", source_ref="",
    )
    fields.update(over)
    row = WordReview(**fields)
    db.add(row)
    db.commit()
    return row


# ── POST /api/review/register-lesson ──────────────────────────────────

def test_register_lesson_no_items_404(client):
    resp = client.post("/api/review/register-lesson", json={
        "subject": "English", "textbook": "Voca_8000", "lesson": "Nonexistent_99",
    })
    assert resp.status_code == 404


def test_register_lesson_registers_all_items(client, db_session):
    _seed_study_items(db_session, lesson="Lesson_REG", n=3)
    resp = client.post("/api/review/register-lesson", json={
        "subject": "English", "textbook": "Voca_8000", "lesson": "Lesson_REG",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered"] == 3
    assert body["total_items"] == 3
    assert body["lesson"] == "Lesson_REG"


def test_register_lesson_is_idempotent(client, db_session):
    """Re-registering the same lesson does not duplicate rows."""
    _seed_study_items(db_session, lesson="Lesson_IDEM", n=2)
    first = client.post("/api/review/register-lesson", json={
        "subject": "English", "textbook": "Voca_8000", "lesson": "Lesson_IDEM",
    })
    assert first.json()["registered"] == 2
    second = client.post("/api/review/register-lesson", json={
        "subject": "English", "textbook": "Voca_8000", "lesson": "Lesson_IDEM",
    })
    # Second call finds existing rows → registers 0
    assert second.json()["registered"] == 0


# ── POST /api/review/register-words ───────────────────────────────────

def test_register_words_bad_source_400(client):
    resp = client.post("/api/review/register-words", json={
        "source": "invalid_source", "words": [{"word": "x"}],
    })
    assert resp.status_code == 400


def test_register_words_daily(client):
    resp = client.post("/api/review/register-words", json={
        "source": "daily", "source_ref": "grade_3/week_1",
        "words": [
            {"word": "brave", "question": "having courage", "hint": "A brave knight."},
            {"word": "quiet", "question": "making little noise", "hint": ""},
        ],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered"] == 2
    assert body["source"] == "daily"


def test_register_words_dedup(client):
    """Same (source, source_ref, word) is not re-registered."""
    payload = {
        "source": "my", "source_ref": "list_A",
        "words": [{"word": "dedup_word", "question": "q"}],
    }
    client.post("/api/review/register-words", json=payload)
    second = client.post("/api/review/register-words", json=payload)
    assert second.json()["registered"] == 0


# ── GET /api/review/today ─────────────────────────────────────────────

def test_today_empty(client):
    resp = client.get("/api/review/today")
    assert resp.status_code == 200
    body = resp.json()
    assert "date" in body and "count" in body and "reviews" in body
    assert isinstance(body["reviews"], list)


def test_today_includes_due_word(client, db_session):
    """A WordReview due today (daily source) appears in the queue."""
    _seed_word_review(db_session, word="duetoday", source="daily")
    resp = client.get("/api/review/today")
    assert resp.status_code == 200
    words = {r["word"] for r in resp.json()["reviews"]}
    assert "duetoday" in words


def test_today_excludes_future_word(client, db_session):
    """A WordReview scheduled in the future is NOT in today's queue."""
    future = (date.today() + timedelta(days=10)).isoformat()
    _seed_word_review(db_session, word="futureword", next_review=future)
    resp = client.get("/api/review/today")
    words = {r["word"] for r in resp.json()["reviews"]}
    assert "futureword" not in words


# ── POST /api/review/result ───────────────────────────────────────────

def test_result_review_not_found_404(client):
    resp = client.post("/api/review/result", json={
        "review_id": 999999, "is_correct": True,
    })
    assert resp.status_code == 404


def test_result_correct_reschedules_forward(client, db_session):
    """A correct answer advances SM-2: interval grows, next_review moves out."""
    row = _seed_word_review(db_session, word="sm2word", source="daily")
    resp = client.post("/api/review/result", json={
        "review_id": row.id, "is_correct": True, "attempts": 1,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["review_id"] == row.id
    assert body["repetitions"] == 1
    # next_review must be strictly after today
    assert body["next_review"] > date.today().isoformat()


def test_result_wrong_resets_repetitions(client, db_session):
    """A wrong answer resets SM-2 repetitions to 0."""
    row = _seed_word_review(db_session, word="wrongword", source="daily",
                            repetitions=3, interval=15)
    resp = client.post("/api/review/result", json={
        "review_id": row.id, "is_correct": False, "attempts": 2,
    })
    assert resp.status_code == 200
    assert resp.json()["repetitions"] == 0


# ── GET /api/review/stats ─────────────────────────────────────────────

def test_stats_empty(client):
    resp = client.get("/api/review/stats")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_words", "due_today", "mastered", "learning",
                "struggling_words"):
        assert key in body


def test_stats_counts_reflect_seed(client, db_session):
    """Seeded rows are reflected in total/due/mastered counts."""
    _seed_word_review(db_session, word="stat_due", source="daily")
    _seed_word_review(db_session, word="stat_mastered", source="daily",
                      repetitions=6, total_reviews=8, total_correct=8)
    resp = client.get("/api/review/stats")
    body = resp.json()
    assert body["total_words"] >= 2
    assert body["mastered"] >= 1   # repetitions >= 5
    assert body["due_today"] >= 1
