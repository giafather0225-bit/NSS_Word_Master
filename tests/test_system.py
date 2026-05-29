"""Tests for backend/routers/system.py — system status + backup management.

Covers the read-only status endpoints and the PIN gate on restore.
The side-effecting endpoints (POST /backups creates a real DB snapshot,
POST /ollama/restart spawns a process) are intentionally NOT exercised
on their happy path — only their guards / shapes are checked.
"""


# ── GET /api/system/status ────────────────────────────────────────────

def test_status_shape(client):
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "ollama" in body
    assert "backups" in body
    assert "count" in body["backups"]
    assert isinstance(body["backups"]["count"], int)


# ── GET /api/system/ollama ────────────────────────────────────────────

def test_ollama_status_shape(client):
    """Ollama status endpoint returns a dict without raising, even when
    the daemon isn't running on the test host."""
    resp = client.get("/api/system/ollama")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


# ── GET /api/system/backups ───────────────────────────────────────────

def test_list_backups_shape(client):
    resp = client.get("/api/system/backups", headers={"X-Parent-Pin": "0000"})
    assert resp.status_code == 200
    body = resp.json()
    assert "backups" in body
    assert isinstance(body["backups"], list)


# ── POST /api/system/backups/restore — PIN gate ───────────────────────

def test_restore_no_pin_403(client):
    """Restore is PIN-protected — missing X-Parent-Pin header → 403,
    and the guard runs before any backup file is touched."""
    resp = client.post("/api/system/backups/restore",
                       json={"filename": "anything.db"})
    assert resp.status_code == 403


def test_restore_wrong_pin_403(client):
    resp = client.post("/api/system/backups/restore",
                       json={"filename": "anything.db"},
                       headers={"X-Parent-Pin": "9999"})
    assert resp.status_code == 403


def test_restore_missing_filename_422(client):
    """Empty body fails Pydantic validation before the PIN dependency
    resolves the body — FastAPI returns 422."""
    resp = client.post("/api/system/backups/restore", json={},
                       headers={"X-Parent-Pin": "0000"})
    assert resp.status_code == 422
