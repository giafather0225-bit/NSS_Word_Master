"""Tests for backend/routers/math_glossary.py."""


def test_get_grades_list(client):
    resp = client.get("/api/math/glossary/grades")
    assert resp.status_code == 200
    grades = {g["grade"] for g in resp.json()["grades"]}
    for g in ("G3", "G4", "G5", "G6"):
        assert g in grades


def test_get_grade_detail(client):
    resp = client.get("/api/math/glossary/g3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["grade"] == "G3"
    assert body["total"] > 0
    assert isinstance(body["categories"], list)
    assert len(body["categories"]) > 0


def test_get_grade_not_found(client):
    resp = client.get("/api/math/glossary/g99")
    assert resp.status_code == 404


def test_get_term(client):
    resp = client.get("/api/math/glossary/g3/addend")
    assert resp.status_code == 200
    term = resp.json()
    assert term["id"] == "addend"
    assert term["term"] == "addend"


def test_term_structure(client):
    resp = client.get("/api/math/glossary/g3/addend")
    assert resp.status_code == 200
    term = resp.json()
    for field in ("id", "term", "category", "definition", "example", "kid_friendly"):
        assert field in term


def test_get_term_not_found(client):
    resp = client.get("/api/math/glossary/g3/nonexistent_term_xyz")
    assert resp.status_code == 404
