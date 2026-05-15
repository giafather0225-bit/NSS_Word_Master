"""Tests for routers/diary_photo.py — diary photo upload / serve / delete.

Upload tests write real files into LEARNING_ROOT/diary_photos/. They all
use the sentinel date 2099-01-01 so the autouse fixture can glob-clean
them without touching real diary photos.
"""
import pytest

from backend.database import LEARNING_ROOT
from backend.models import DiaryEntry

_PHOTO_DIR = LEARNING_ROOT / "diary_photos"
_SENTINEL = "2099-01-01"


@pytest.fixture(autouse=True)
def _clean(db_session):
    def _wipe():
        db_session.query(DiaryEntry).delete()
        db_session.commit()
        for p in _PHOTO_DIR.glob(f"{_SENTINEL}_*"):
            p.unlink(missing_ok=True)
    _wipe()
    yield
    _wipe()


def _png():
    return ("test.png", b"\x89PNG\r\nfake-image-bytes", "image/png")


# ── POST /api/diary/photo ─────────────────────────────────────

def test_upload_invalid_date_400(client):
    r = client.post("/api/diary/photo", data={"entry_date": "not-a-date"},
                    files={"file": _png()})
    assert r.status_code == 400


def test_upload_invalid_extension_400(client):
    r = client.post("/api/diary/photo", data={"entry_date": _SENTINEL},
                    files={"file": ("bad.txt", b"data", "text/plain")})
    assert r.status_code == 400


def test_upload_creates_entry(client, db_session):
    r = client.post("/api/diary/photo", data={"entry_date": _SENTINEL},
                    files={"file": _png()})
    assert r.status_code == 201
    body = r.json()
    assert body["entry_date"] == _SENTINEL
    assert body["photo_url"].startswith("/api/diary/photo/")
    assert db_session.query(DiaryEntry).filter_by(entry_date=_SENTINEL).count() == 1


def test_upload_updates_existing_entry(client, db_session):
    db_session.add(DiaryEntry(entry_date=_SENTINEL, content="hi",
                              photo_path=None, created_at="2099-01-01T00:00:00"))
    db_session.commit()
    r = client.post("/api/diary/photo", data={"entry_date": _SENTINEL},
                    files={"file": _png()})
    assert r.status_code == 201
    db_session.expire_all()
    entry = db_session.query(DiaryEntry).filter_by(entry_date=_SENTINEL).first()
    assert entry.photo_path is not None


# ── POST /api/diary/photo/multi ───────────────────────────────

def test_multi_upload_returns_filename(client):
    r = client.post("/api/diary/photo/multi", data={"entry_date": _SENTINEL},
                    files={"file": _png()})
    assert r.status_code == 201
    body = r.json()
    assert body["filename"].startswith(_SENTINEL)
    assert body["photo_url"].startswith("/api/diary/photo/")


# ── DELETE /api/diary/photo/{filename} ────────────────────────

def test_delete_invalid_filename_400(client):
    # Chars outside [A-Za-z0-9._-] are rejected by _PHOTO_NAME_RE.
    assert client.delete("/api/diary/photo/bad name!.png").status_code == 400


def test_delete_nonexistent_ok(client):
    # Missing file → still 200; endpoint is best-effort + clears DB ref.
    r = client.delete(f"/api/diary/photo/{_SENTINEL}_missing.png")
    assert r.status_code == 200
    assert r.json()["deleted"] == f"{_SENTINEL}_missing.png"


def test_delete_clears_db_reference(client, db_session):
    db_session.add(DiaryEntry(entry_date=_SENTINEL, content="",
                              photo_path=f"{_SENTINEL}_x.png",
                              created_at="2099-01-01T00:00:00"))
    db_session.commit()
    r = client.delete(f"/api/diary/photo/{_SENTINEL}_x.png")
    assert r.status_code == 200
    db_session.expire_all()
    entry = db_session.query(DiaryEntry).filter_by(entry_date=_SENTINEL).first()
    assert entry.photo_path is None


# ── GET /api/diary/photo/{filename} ───────────────────────────

def test_get_invalid_filename_400(client):
    assert client.get("/api/diary/photo/bad name!.png").status_code == 400


def test_get_nonexistent_404(client):
    assert client.get(f"/api/diary/photo/{_SENTINEL}_nope.png").status_code == 404
