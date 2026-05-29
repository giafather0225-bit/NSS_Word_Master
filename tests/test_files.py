"""Tests for routers/files.py — per-lesson file storage + OCR trigger.

Covers the DB-validation / error paths (missing lesson 404, lang
validation 400, empty file list). The OCR pipeline and actual byte
storage are exercised by tests/test_file_storage.py.
"""
import pytest

from backend.models import Lesson


@pytest.fixture(autouse=True)
def _clean(db_session):
    db_session.query(Lesson).delete()
    db_session.commit()
    yield
    db_session.query(Lesson).delete()
    db_session.commit()


@pytest.fixture
def lesson(db_session):
    from datetime import datetime, timezone
    l = Lesson(subject="English", textbook="Voca_8000", lesson_name="Lesson_01",
               source_type="manual", description="",
               created_at=datetime.now(timezone.utc).isoformat())
    db_session.add(l)
    db_session.commit()
    db_session.refresh(l)
    return l


def _png():
    # Full 8-byte PNG signature (\x89PNG\r\n\x1a\n) + filler. file_storage.py
    # validates the complete signature, not just the \x89PNG\r\n prefix.
    return {"file": ("x.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 8, "image/png")}


def _spoofed_png():
    """JPEG magic bytes disguised as .png — should be rejected at magic check."""
    return {"file": ("spoof.png", b"\xff\xd8\xff" + b"\x00" * 20, "image/png")}


# ── POST /api/storage/lessons/{id}/files ──────────────────────

def test_upload_missing_lesson_404(client):
    r = client.post("/api/storage/lessons/9999/files", files=_png())
    assert r.status_code == 404


# ── GET /api/storage/lessons/{id}/files ───────────────────────

def test_list_files_missing_lesson_404(client):
    assert client.get("/api/storage/lessons/9999/files").status_code == 404


def test_list_files_empty_for_new_lesson(client, lesson):
    body = client.get(f"/api/storage/lessons/{lesson.id}/files").json()
    assert body["lesson_id"] == lesson.id
    assert body["count"] == 0
    assert body["files"] == []


# ── DELETE /api/storage/lessons/{id}/files/{filename} ─────────

def test_delete_file_missing_lesson_404(client):
    r = client.delete("/api/storage/lessons/9999/files/x.png")
    assert r.status_code == 404


def test_delete_missing_file_404(client, lesson):
    r = client.delete(f"/api/storage/lessons/{lesson.id}/files/nope.png")
    assert r.status_code == 404


# ── POST /api/storage/lessons/{id}/ocr ────────────────────────

def test_ocr_invalid_lang_400(client, lesson):
    # _validate_lang runs before the lesson lookup — ';' is rejected.
    r = client.post(f"/api/storage/lessons/{lesson.id}/ocr?lang=eng;rm")
    assert r.status_code == 400


def test_ocr_missing_lesson_404(client):
    r = client.post("/api/storage/lessons/9999/ocr?lang=eng")
    assert r.status_code == 404


# ── Magic-byte rejection — POST /api/storage/lessons/{id}/files ──

def test_upload_lesson_file_magic_mismatch_400(client, lesson):
    """Extension is .png but content starts with JPEG magic — rejected 400."""
    r = client.post(
        f"/api/storage/lessons/{lesson.id}/files",
        files=_spoofed_png(),
    )
    assert r.status_code == 400


def test_upload_lesson_file_valid_png_accepted(client, lesson):
    """Correct PNG magic bytes pass the check (file reaches save_lesson_file)."""
    r = client.post(
        f"/api/storage/lessons/{lesson.id}/files",
        files=_png(),
    )
    # 200 OK or 400 from save_lesson_file (stub bytes fail HEIC/PIL conversion)
    # — important is that magic check itself did NOT fire a 400 for this path.
    # A real PNG stub may fail downstream but never with "does not match".
    if r.status_code == 400:
        assert "does not match" not in r.json().get("detail", "")
