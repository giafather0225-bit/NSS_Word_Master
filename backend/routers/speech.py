"""
routers/speech.py — Local speech-to-text for offline Shadow stage
Section: English / Speech
Dependencies: faster-whisper (lazy-loaded)
API: POST /api/speech/recognize
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded Whisper model (CPU-friendly tiny/base model)
_WHISPER_MODEL = None
_WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base.en")


def _get_model():
    """
    Lazy-init faster-whisper model. Returns None if faster-whisper is not
    installed, so callers can gracefully fall back.
    @tag SPEECH OFFLINE
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper not installed — offline speech unavailable")
        return None
    try:
        _WHISPER_MODEL = WhisperModel(
            _WHISPER_MODEL_NAME,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Loaded Whisper model: %s", _WHISPER_MODEL_NAME)
        return _WHISPER_MODEL
    except Exception as exc:
        logger.error("Failed to load Whisper model: %s", exc)
        return None


@router.post("/api/speech/recognize")
async def recognize_speech(
    audio: UploadFile = File(...),
    lang: Optional[str] = Form("en"),
):
    """
    Transcribe an uploaded audio clip with local Whisper.
    Used by Shadow/Sentence-Reading stages when the browser's online
    Web Speech API is unavailable (offline / privacy).

    Body: multipart/form-data with `audio` (webm/ogg/wav) and optional `lang`.
    Returns: {"transcript": str, "model": str}
    @tag SPEECH OFFLINE
    """
    model = _get_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Offline speech recognition not available. Install faster-whisper.",
        )

    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    try:
        data = await audio.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty audio upload")
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            segments, _info = model.transcribe(
                tmp_path,
                language=lang or "en",
                beam_size=1,
                vad_filter=True,
            )
            transcript = " ".join(seg.text.strip() for seg in segments).strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return {"transcript": transcript, "model": _WHISPER_MODEL_NAME}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"transcription failed: {exc}")
