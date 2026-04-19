"""
routers/tts.py — Text-to-speech audio generation routes (all return MP3 bytes)
Section: English
Dependencies: tts_edge (edge-tts → BytesIO), concurrent.futures
API:
  POST /api/tts/preview_sequence      → MP3 bytes
  POST /api/tts/preview_word_meaning  → MP3 bytes
  POST /api/tts/word_meaning          → MP3 bytes
  POST /api/tts/word_only             → MP3 bytes
  POST /api/tts/example_full          → MP3 bytes
  POST /api/tts                       → MP3 bytes

Server never plays audio on its own speakers — browser receives MP3 and plays
via fetch → Blob → HTMLAudioElement. This lets the child study on any device
(iPad / phone / other computer) while the backend runs on the parent's Mac.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from backend.tts_edge import (
    preview_sequence_bytes,
    preview_word_meaning_bytes,
    word_meaning_bytes,
    word_only_bytes,
    example_full_bytes,
    line_bytes,
)

router = APIRouter()

# Larger pool: every request does a blocking edge-tts network call. With only 2
# workers, rapid taps (common with kids) would queue and feel like a freeze.
_executor = ThreadPoolExecutor(max_workers=8)


# ── Pydantic Schemas ───────────────────────────────────────

class TTSLineRequest(BaseModel):
    text: str

    def clean(self):
        """Sanitize text input."""
        self.text = self.text.strip()[:500]
        return self


class PreviewTTSRequest(BaseModel):
    word: str
    meaning: str
    example: str

    def clean(self):
        """Sanitize all preview TTS fields."""
        self.word    = self.word.strip()[:100]
        self.meaning = self.meaning.strip()[:300]
        self.example = self.example.strip()[:500]
        return self


class WordMeaningTTSRequest(BaseModel):
    word: str
    meaning: str
    rep: int = 1  # repetition number 1-3 for varied friendly phrases

    def clean(self):
        """Sanitize word/meaning and clamp rep to [1, 3]."""
        self.word    = self.word.strip()[:100]
        self.meaning = self.meaning.strip()[:300]
        self.rep     = max(1, min(3, self.rep))
        return self


class TTSWordOnlyRequest(BaseModel):
    word: str

    def clean(self):
        """Sanitize word field."""
        self.word = self.word.strip()[:100]
        return self


class TTSExampleFullRequest(BaseModel):
    sentence: str

    def clean(self):
        """Sanitize sentence field."""
        self.sentence = self.sentence.strip()[:500]
        return self


# ── Routes ─────────────────────────────────────────────────

async def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: fn(*args))


# @tag TTS @tag PREVIEW
@router.post("/api/tts/preview_sequence")
async def tts_preview_sequence(req: PreviewTTSRequest):
    """Return MP3 bytes for the preview sequence: word → meaning → example."""
    req.clean()
    audio = await _run(preview_sequence_bytes, req.word, req.meaning, req.example)
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS @tag PREVIEW
@router.post("/api/tts/preview_word_meaning")
async def tts_preview_word_meaning(req: WordMeaningTTSRequest):
    """Return MP3 bytes for word (normal speed) → meaning (slow); call 3× for repetition."""
    req.clean()
    audio = await _run(preview_word_meaning_bytes, req.word, req.meaning, req.rep)
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts/word_meaning")
async def tts_word_meaning(req: WordMeaningTTSRequest):
    """Return MP3 bytes for word then meaning."""
    req.clean()
    audio = await _run(word_meaning_bytes, req.word, req.meaning)
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts/word_only")
async def tts_word_only(req: TTSWordOnlyRequest):
    """Return MP3 bytes for a single word spoken aloud."""
    req.clean()
    audio = await _run(word_only_bytes, req.word)
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts/example_full")
async def tts_example_full(req: TTSExampleFullRequest):
    """Return MP3 bytes for a full example sentence."""
    req.clean()
    audio = await _run(example_full_bytes, req.sentence)
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts")
async def play_tts_line(req: TTSLineRequest):
    """Return MP3 bytes for a single line of narration."""
    req.clean()
    audio = await _run(line_bytes, req.text)
    return Response(content=audio, media_type="audio/mpeg")
