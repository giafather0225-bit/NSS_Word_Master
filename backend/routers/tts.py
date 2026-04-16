"""
routers/tts.py — Text-to-speech audio generation routes
Section: English
Dependencies: tts_edge (primary), tts_say (fallback), concurrent.futures
API:
  POST /api/tts/preview_sequence
  POST /api/tts/preview_word_meaning
  POST /api/tts/word_meaning
  POST /api/tts/word_only
  POST /api/tts/example_full
  POST /api/tts
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

try:
    from tts_edge import (
        say_preview_sequence,
        say_preview_word_meaning,
        say_word_then_meaning,
        say_line,
        say_word_twice,
        say_full_sentence,
        say_example_with_intro,
        preview_word_meaning_bytes,
        example_full_bytes,
        word_only_bytes,
        word_meaning_bytes,
        preview_sequence_bytes,
    )
except ImportError:
    from tts_say import (  # type: ignore[assignment]
        say_preview_sequence,
        say_preview_word_meaning,
        say_word_then_meaning,
        say_line,
        say_word_twice,
        say_full_sentence,
    )
    def say_example_with_intro(example: str) -> None:  # type: ignore[misc]
        say_full_sentence(example)

router = APIRouter()

_executor = ThreadPoolExecutor(max_workers=2)


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

# @tag TTS @tag PREVIEW
@router.post("/api/tts/preview_sequence")
async def tts_preview_sequence(req: PreviewTTSRequest):
    """Play word → meaning → example sentence as a TTS sequence (no audio bytes returned)."""
    req.clean()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor,
        lambda: say_preview_sequence(req.word, req.meaning, req.example),
    )
    return Response(status_code=200)


# @tag TTS @tag PREVIEW
@router.post("/api/tts/preview_word_meaning")
async def tts_preview_word_meaning(req: WordMeaningTTSRequest):
    """Return MP3 bytes for word (normal speed) → meaning (slow); call 3× for repetition."""
    req.clean()
    loop = asyncio.get_event_loop()
    audio = await loop.run_in_executor(
        _executor,
        lambda: preview_word_meaning_bytes(req.word, req.meaning, req.rep),
    )
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts/word_meaning")
async def tts_word_meaning(req: WordMeaningTTSRequest):
    """Play word then meaning via TTS (no audio bytes returned)."""
    req.clean()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor,
        lambda: say_word_then_meaning(req.word, req.meaning),
    )
    return Response(status_code=200)


# @tag TTS
@router.post("/api/tts/word_only")
async def tts_word_only(req: TTSWordOnlyRequest):
    """Return MP3 bytes for a single word spoken aloud."""
    req.clean()
    loop = asyncio.get_event_loop()
    audio = await loop.run_in_executor(
        _executor,
        lambda: word_only_bytes(req.word),
    )
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts/example_full")
async def tts_example_full(req: TTSExampleFullRequest):
    """Return MP3 bytes for a full example sentence."""
    req.clean()
    loop = asyncio.get_event_loop()
    audio = await loop.run_in_executor(
        _executor,
        lambda: example_full_bytes(req.sentence),
    )
    return Response(content=audio, media_type="audio/mpeg")


# @tag TTS
@router.post("/api/tts")
async def play_tts_line(req: TTSLineRequest):
    """Play a single line of text (overlay narration etc.) via TTS."""
    req.clean()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, lambda: say_line(req.text))
    return Response(status_code=200)
