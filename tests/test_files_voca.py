"""Tests for routers/files_voca.py — voca folder upload + serve + delete.

Focuses on the magic-byte rejection path added in the security hardening
pass (P1 #3). The folder-upload endpoint silently skips bad files and
returns them in the ``skipped`` list rather than raising an HTTP error,
so assertions target that field.
"""
import pytest

from backend.database import LEARNING_ROOT


_SENTINEL_LESSON = "Lesson_99"
_VOCA_ROOT = LEARNING_ROOT / "English" / "Voca_8000" / _SENTINEL_LESSON


@pytest.fixture(autouse=True)
def _clean():
    """Remove any sentinel files written during a test run."""
    yield
    if _VOCA_ROOT.exists():
        for p in _VOCA_ROOT.iterdir():
            p.unlink(missing_ok=True)
        try:
            _VOCA_ROOT.rmdir()
        except OSError:
            pass


def _file(name: str, data: bytes, mime: str = "image/png"):
    return ("files", (name, data, mime))


# ── POST /api/voca/folder-upload/{lesson} ────────────────────

def test_valid_png_accepted(client):
    """A file with correct PNG magic bytes is saved and returned in ``saved``."""
    r = client.post(
        f"/api/voca/folder-upload/{_SENTINEL_LESSON}",
        files=[_file("ok.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)],
    )
    assert r.status_code == 200
    body = r.json()
    assert "ok.png" in body["saved"]
    assert body["count"] >= 1


def test_magic_mismatch_png_ext_skipped(client):
    """JPEG bytes named .png — magic check skips the file (no 400 raised)."""
    r = client.post(
        f"/api/voca/folder-upload/{_SENTINEL_LESSON}",
        files=[_file("spoof.png", b"\xff\xd8\xff" + b"\x00" * 20)],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert any("spoof.png" in s for s in body["skipped"])
    assert any("content does not match" in s for s in body["skipped"])


def test_magic_mismatch_jpg_ext_skipped(client):
    """PNG bytes named .jpg — magic check skips the file."""
    r = client.post(
        f"/api/voca/folder-upload/{_SENTINEL_LESSON}",
        files=[_file("spoof.jpg", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "image/jpeg")],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert any("spoof.jpg" in s for s in body["skipped"])


def test_mixed_batch_only_valid_saved(client):
    """In a mixed batch, valid files are saved and spoofed files are skipped."""
    r = client.post(
        f"/api/voca/folder-upload/{_SENTINEL_LESSON}",
        files=[
            _file("good.png",  b"\x89PNG\r\n\x1a\n" + b"\x00" * 20),
            _file("spoof.png", b"\xff\xd8\xff"      + b"\x00" * 20),
        ],
    )
    assert r.status_code == 200
    body = r.json()
    assert "good.png" in body["saved"]
    assert body["count"] == 1
    assert any("spoof.png" in s for s in body["skipped"])


def test_disallowed_extension_skipped(client):
    """A .txt file is rejected before the magic check (ext not in allowed list)."""
    r = client.post(
        f"/api/voca/folder-upload/{_SENTINEL_LESSON}",
        files=[_file("note.txt", b"hello", "text/plain")],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert any("note.txt" in s for s in body["skipped"])


# ── Invalid lesson key ────────────────────────────────────────

def test_invalid_lesson_key_400(client):
    """A lesson name with path-traversal characters is rejected immediately."""
    r = client.post(
        "/api/voca/folder-upload/../../../etc",
        files=[_file("x.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)],
    )
    assert r.status_code in (400, 404)
