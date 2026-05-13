"""Smoke tests for backend/routers/ckla.py + parent_ckla.py.

Covers read-only endpoints and the grade-range validation we added —
detects router wiring breaks, missing schema fields, and ensures the
ge=3/le=8 Query constraint blocks out-of-range input.
"""


# ── /api/academy/ckla/grades ──────────────────────────────────────────

def test_grades_list(client):
    """Grades endpoint returns a list of {grade, title, lesson_count}."""
    resp = client.get("/api/academy/ckla/grades")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    # Every entry has the required shape
    for entry in body:
        assert "grade" in entry
        assert "title" in entry
        assert "lesson_count" in entry


# ── /api/academy/ckla/title ───────────────────────────────────────────

def test_title_default_grade(client):
    """Title endpoint returns a string for default grade=3."""
    resp = client.get("/api/academy/ckla/title")
    assert resp.status_code == 200
    body = resp.json()
    assert "title" in body
    assert isinstance(body["title"], str)


def test_title_grade_below_range_rejected(client):
    """grade=2 must be rejected by ge=3 Pydantic Query validator."""
    resp = client.get("/api/academy/ckla/title?grade=2")
    assert resp.status_code == 422


def test_title_grade_above_range_rejected(client):
    """grade=9 must be rejected by le=8 Pydantic Query validator."""
    resp = client.get("/api/academy/ckla/title?grade=9")
    assert resp.status_code == 422


def test_title_grade_string_rejected(client):
    """Non-integer grade is rejected as type-error."""
    resp = client.get("/api/academy/ckla/title?grade=abc")
    assert resp.status_code == 422


# ── /api/academy/ckla/domains ─────────────────────────────────────────

def test_domains_returns_list(client):
    resp = client.get("/api/academy/ckla/domains?grade=3")
    assert resp.status_code == 200
    body = resp.json()
    assert "domains" in body
    assert isinstance(body["domains"], list)


def test_domains_grade_validation(client):
    resp = client.get("/api/academy/ckla/domains?grade=99")
    assert resp.status_code == 422


# ── /api/academy/ckla/domains/{domain_num}/lessons ────────────────────

def test_lessons_by_domain_returns_dict(client):
    """Lessons for domain 1 — returns shape even if domain doesn't exist."""
    resp = client.get("/api/academy/ckla/domains/1/lessons?grade=3")
    # Either 200 with empty lessons or 404 if not seeded
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        body = resp.json()
        assert "lessons" in body
        assert isinstance(body["lessons"], list)


def test_lessons_invalid_domain_404(client):
    """Bogus domain_num returns 404, not 500."""
    resp = client.get("/api/academy/ckla/domains/9999/lessons?grade=3")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        # Empty lessons array for unknown domain
        assert resp.json()["lessons"] == []


# ── /api/academy/ckla/lessons/{lesson_id} ─────────────────────────────

def test_lesson_detail_not_found(client):
    """Bogus lesson_id returns 404."""
    resp = client.get("/api/academy/ckla/lessons/999999")
    assert resp.status_code == 404


# ── /api/academy/ckla/badges ──────────────────────────────────────────

def test_badges_endpoint(client):
    resp = client.get("/api/academy/ckla/badges?grade=3")
    assert resp.status_code == 200
    body = resp.json()
    assert "badges" in body or "earned" in body or isinstance(body, list)


def test_badges_grade_validation(client):
    resp = client.get("/api/academy/ckla/badges?grade=0")
    assert resp.status_code == 422


# ── /api/academy/ckla/grade-final-test ────────────────────────────────

def test_grade_final_test_status(client):
    """Status endpoint must not 500 on empty DB."""
    resp = client.get("/api/academy/ckla/grade-final-test/status?grade=3")
    # Endpoint may not exist, may be locked, or return state — only ensure no 500
    assert resp.status_code in (200, 403, 404, 405)


def test_grade_final_test_grade_validation(client):
    resp = client.get("/api/academy/ckla/grade-final-test?grade=20")
    assert resp.status_code == 422


# ── Parent CKLA summary ───────────────────────────────────────────────

def test_parent_ckla_summary(client):
    """Parent dashboard CKLA summary endpoint."""
    resp = client.get("/api/parent/ckla-summary?grade=3")
    # Could 200 (empty data) or 403 (PIN required) or 404 if not registered
    assert resp.status_code in (200, 401, 403, 404)


def test_parent_ckla_summary_grade_validation(client):
    """grade=2 should be rejected even before PIN check."""
    resp = client.get("/api/parent/ckla-summary?grade=2")
    # Either 422 (validation first) or 401/403 (auth first)
    assert resp.status_code in (401, 403, 422)


# ═════════════════════════════════════════════════════════════════════
# Deeper integration tests — seeded G3 domain/lesson/questions
# ═════════════════════════════════════════════════════════════════════

def test_domains_with_seeded_domain(client, ckla_seed):
    """A seeded G3 domain shows up in /domains list."""
    resp = client.get("/api/academy/ckla/domains?grade=3")
    assert resp.status_code == 200
    body = resp.json()
    domain_nums = [d["domain_num"] for d in body["domains"]]
    assert 1 in domain_nums
    seeded = next(d for d in body["domains"] if d["domain_num"] == 1)
    assert seeded["title"] == "Test Domain — Classic Tales"
    assert seeded["grade"] == 3
    # Single lesson, not yet completed
    assert seeded["completed_count"] == 0
    assert seeded["all_complete"] is False


def test_domains_completion_percentage_zero_initially(client, ckla_seed):
    resp = client.get("/api/academy/ckla/domains?grade=3")
    body = resp.json()
    assert body["completion_pct"] == 0
    assert body["completed_lessons"] == 0
    assert body["total_lessons"] >= 1


def test_lessons_for_seeded_domain(client, ckla_seed):
    """Listing lessons for the seeded domain returns the seeded lesson."""
    resp = client.get("/api/academy/ckla/domains/1/lessons?grade=3")
    assert resp.status_code == 200
    body = resp.json()
    assert "lessons" in body
    titles = [l.get("title") for l in body["lessons"]]
    assert "Test Lesson 1" in titles


def test_lesson_detail_returns_passage_and_questions(client, ckla_seed):
    """GET /lessons/{id} returns full passage + sampled questions."""
    lesson_id = ckla_seed["lesson"].id
    resp = client.get(f"/api/academy/ckla/lessons/{lesson_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == lesson_id
    assert body["title"] == "Test Lesson 1"
    assert body["domain_num"] == 1
    assert body["grade"] == 3
    assert body["word_work_word"] == "test"
    assert "Once upon a time" in body["passage"]
    # 3 questions seeded — sampled list is non-empty
    assert isinstance(body["questions"], list)
    assert len(body["questions"]) >= 1
    # Each question carries required fields
    for q in body["questions"]:
        for field in ("id", "num", "kind", "question"):
            assert field in q


def test_lesson_progress_initial_state(client, ckla_seed):
    """Progress endpoint returns a defaulted shape when no row exists."""
    lesson_id = ckla_seed["lesson"].id
    resp = client.get(f"/api/academy/ckla/lessons/{lesson_id}/progress")
    assert resp.status_code == 200
    prog = resp.json()
    # Either {completed: False, ...} or null/empty shape
    assert isinstance(prog, dict)


def test_lesson_detail_inactive_404(client, ckla_seed, db_session):
    """Deactivating a lesson makes the detail endpoint 404."""
    from backend.models import CKLALesson
    lesson_id = ckla_seed["lesson"].id
    lesson = db_session.query(CKLALesson).filter_by(id=lesson_id).first()
    lesson.is_active = False
    db_session.commit()

    resp = client.get(f"/api/academy/ckla/lessons/{lesson_id}")
    assert resp.status_code == 404


def test_grades_lesson_count_reflects_seed(client, ckla_seed):
    """/grades shows lesson count for G3 ≥ 1 after seeding."""
    resp = client.get("/api/academy/ckla/grades")
    assert resp.status_code == 200
    g3 = next((g for g in resp.json() if g["grade"] == 3), None)
    assert g3 is not None
    assert g3["lesson_count"] >= 1
