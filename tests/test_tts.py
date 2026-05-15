"""Tests for routers/tts.py — input validation + TTS-backend error paths.

Network calls (edge-tts) are mocked so tests run offline.  We cover:
  - 422 for missing required fields
  - 503 when the TTS helper returns empty bytes
  - 503 when the TTS helper raises an unexpected exception
"""
from unittest.mock import patch

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _mock_empty(_executor, *_args):
    """Simulate edge-tts returning empty bytes → 503."""
    return b""


_PREVIEW_BODY = {"word": "run", "meaning": "to move fast", "example": "She runs daily."}
_WM_BODY = {"word": "run", "meaning": "to move fast", "rep": 1}
_WORD_BODY = {"word": "run"}
_EXAMPLE_BODY = {"sentence": "She runs every day."}
_LINE_BODY = {"text": "Hello world."}


# ── POST /api/tts/preview_sequence ───────────────────────────────────────────

def test_preview_sequence_422_missing_word(client):
    r = client.post("/api/tts/preview_sequence", json={"meaning": "x", "example": "y"})
    assert r.status_code == 422


def test_preview_sequence_503_on_empty_audio(client):
    with patch("backend.routers.tts.preview_sequence_bytes", return_value=b""):
        r = client.post("/api/tts/preview_sequence", json=_PREVIEW_BODY)
    assert r.status_code == 503


def test_preview_sequence_503_on_exception(client):
    with patch("backend.routers.tts.preview_sequence_bytes", side_effect=RuntimeError("boom")):
        r = client.post("/api/tts/preview_sequence", json=_PREVIEW_BODY)
    assert r.status_code == 503


def test_preview_sequence_success(client):
    with patch("backend.routers.tts.preview_sequence_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts/preview_sequence", json=_PREVIEW_BODY)
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"


# ── POST /api/tts/preview_word_meaning ───────────────────────────────────────

def test_preview_word_meaning_422_missing_meaning(client):
    r = client.post("/api/tts/preview_word_meaning", json={"word": "run"})
    assert r.status_code == 422


def test_preview_word_meaning_503_on_empty_audio(client):
    with patch("backend.routers.tts.preview_word_meaning_bytes", return_value=b""):
        r = client.post("/api/tts/preview_word_meaning", json=_WM_BODY)
    assert r.status_code == 503


def test_preview_word_meaning_success(client):
    with patch("backend.routers.tts.preview_word_meaning_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts/preview_word_meaning", json=_WM_BODY)
    assert r.status_code == 200


# ── POST /api/tts/word_meaning ────────────────────────────────────────────────

def test_word_meaning_422_missing_fields(client):
    r = client.post("/api/tts/word_meaning", json={"word": "run"})
    assert r.status_code == 422


def test_word_meaning_503_on_exception(client):
    with patch("backend.routers.tts.word_meaning_bytes", side_effect=OSError("net")):
        r = client.post("/api/tts/word_meaning", json=_WM_BODY)
    assert r.status_code == 503


def test_word_meaning_success(client):
    with patch("backend.routers.tts.word_meaning_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts/word_meaning", json=_WM_BODY)
    assert r.status_code == 200


# ── POST /api/tts/word_only ───────────────────────────────────────────────────

def test_word_only_422_missing_word(client):
    r = client.post("/api/tts/word_only", json={})
    assert r.status_code == 422


def test_word_only_503_on_empty_audio(client):
    with patch("backend.routers.tts.word_only_bytes", return_value=b""):
        r = client.post("/api/tts/word_only", json=_WORD_BODY)
    assert r.status_code == 503


def test_word_only_success(client):
    with patch("backend.routers.tts.word_only_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts/word_only", json=_WORD_BODY)
    assert r.status_code == 200


# ── POST /api/tts/example_full ───────────────────────────────────────────────

def test_example_full_422_missing_sentence(client):
    r = client.post("/api/tts/example_full", json={})
    assert r.status_code == 422


def test_example_full_503_on_empty_audio(client):
    with patch("backend.routers.tts.example_full_bytes", return_value=b""):
        r = client.post("/api/tts/example_full", json=_EXAMPLE_BODY)
    assert r.status_code == 503


def test_example_full_success(client):
    with patch("backend.routers.tts.example_full_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts/example_full", json=_EXAMPLE_BODY)
    assert r.status_code == 200


# ── POST /api/tts ─────────────────────────────────────────────────────────────

def test_tts_line_422_missing_text(client):
    r = client.post("/api/tts", json={})
    assert r.status_code == 422


def test_tts_line_503_on_empty_audio(client):
    with patch("backend.routers.tts.line_bytes", return_value=b""):
        r = client.post("/api/tts", json=_LINE_BODY)
    assert r.status_code == 503


def test_tts_line_503_on_exception(client):
    with patch("backend.routers.tts.line_bytes", side_effect=ConnectionError("offline")):
        r = client.post("/api/tts", json=_LINE_BODY)
    assert r.status_code == 503


def test_tts_line_success(client):
    with patch("backend.routers.tts.line_bytes", return_value=b"\xFF\xFB" + b"\x00" * 100):
        r = client.post("/api/tts", json=_LINE_BODY)
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
