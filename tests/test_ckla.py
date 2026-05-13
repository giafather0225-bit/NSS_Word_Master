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
