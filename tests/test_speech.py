"""Tests for routers/speech.py — offline Whisper STT endpoint.

faster-whisper is NOT installed in CI, so _get_model() returns None and the
endpoint raises 503.  We cover that path plus the 400/413 validation paths
by patching _get_model to return a minimal stub when needed.
"""
from io import BytesIO
from unittest.mock import MagicMock, patch


# ── 503 — model unavailable (faster-whisper not installed / default CI) ──────

def test_recognize_503_when_no_model(client):
    with patch("backend.routers.speech._get_model", return_value=None):
        r = client.post(
            "/api/speech/recognize",
            files={"audio": ("clip.webm", b"\x1a\x45\xdf\xa3", "audio/webm")},
        )
    assert r.status_code == 503
    assert "not available" in r.json()["detail"].lower()


# ── 400 — empty audio body ────────────────────────────────────────────────────

def _stub_model():
    """Minimal Whisper stub: transcribe returns ([], info)."""
    m = MagicMock()
    m.transcribe.return_value = ([], MagicMock())
    return m


def test_recognize_400_empty_audio(client):
    with patch("backend.routers.speech._get_model", return_value=_stub_model()):
        r = client.post(
            "/api/speech/recognize",
            files={"audio": ("clip.webm", b"", "audio/webm")},
        )
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


# ── 413 — audio file too large ───────────────────────────────────────────────

def test_recognize_413_oversized_audio(client):
    big = b"\x00" * (10_000_001)   # 1 byte over 10 MB limit
    with patch("backend.routers.speech._get_model", return_value=_stub_model()):
        r = client.post(
            "/api/speech/recognize",
            files={"audio": ("clip.wav", big, "audio/wav")},
        )
    assert r.status_code == 413


# ── 200 — happy path with stubbed model ──────────────────────────────────────

def test_recognize_returns_transcript(client):
    seg = MagicMock()
    seg.text = "hello world"
    model = MagicMock()
    model.transcribe.return_value = ([seg], MagicMock())

    with patch("backend.routers.speech._get_model", return_value=model):
        r = client.post(
            "/api/speech/recognize",
            files={"audio": ("clip.webm", b"\x1a\x45\xdf\xa3fake", "audio/webm")},
            data={"lang": "en"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["transcript"] == "hello world"
    assert "model" in body
