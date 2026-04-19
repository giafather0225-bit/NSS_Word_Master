"""Microsoft Edge TTS — neural voices (Jenny/Aria). Much more natural than macOS say.
Requires: pip3 install edge-tts  +  internet connection.
Voice options: en-US-JennyNeural, en-US-AriaNeural, en-US-GuyNeural
Override with TTS_VOICE_EDGE env var.

All output is returned as in-memory MP3 bytes for the browser to play
via fetch → Blob → Audio. No server-side speaker playback (no `say`, no `afplay`).
"""
from __future__ import annotations

import asyncio
import io
import os

import edge_tts

VOICE = os.environ.get("TTS_VOICE_EDGE", "en-US-JennyNeural")

# Speech rate: "+0%" = normal, "-10%" = 10% slower, "+10%" = 10% faster
RATE_WORD    = os.environ.get("TTS_EDGE_RATE_WORD",    "-5%")
RATE_MEANING = os.environ.get("TTS_EDGE_RATE_MEANING", "-12%")
RATE_EXAMPLE = os.environ.get("TTS_EDGE_RATE_EXAMPLE", "-8%")

# Friendly phrases per repetition (0-indexed)
_PREVIEW_SETS = [
    ("",                  "This means"),
    ("Let's go again —",  "And it means"),
    ("One more time!",    "So"),
]

_EXAMPLE_INTRO = "Now let me show you this word in a real sentence."


# ── Core bytes generation ─────────────────────────────────────────────

async def _generate_mp3_bytes(text: str, rate: str) -> bytes:
    communicate = edge_tts.Communicate(text, VOICE, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def generate_mp3_bytes(text: str, rate: str = "+0%") -> bytes:
    """Synchronous wrapper: return MP3 bytes for `text` at the given speech rate."""
    t = (text or "").strip()
    if not t:
        return b""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_generate_mp3_bytes(t, rate))
    finally:
        loop.close()


# ── Domain helpers (all return bytes) ─────────────────────────────────

def preview_word_meaning_bytes(word: str, meaning: str, rep: int = 1) -> bytes:
    """One preview study set: (optional intro) word, spelled, meaning. Call 3× from frontend."""
    idx = max(0, min(rep - 1, len(_PREVIEW_SETS) - 1))
    intro, meaning_prefix = _PREVIEW_SETS[idx]
    spelled = ", ".join(word.upper()) if word else ""
    parts: list[str] = []
    if intro:
        parts.append(intro)
    if word:
        parts.append(f"{word}.")
        parts.append(f"{spelled}.")
    if meaning:
        parts.append(f"{meaning_prefix}: {meaning}.")
    return generate_mp3_bytes("  ".join(parts), RATE_MEANING)


def example_full_bytes(sentence: str) -> bytes:
    t = (sentence or "").strip()
    if not t:
        return b""
    return generate_mp3_bytes(f"{_EXAMPLE_INTRO}  {t}", RATE_EXAMPLE)


def word_only_bytes(word: str) -> bytes:
    w = (word or "").strip()
    if not w:
        return b""
    return generate_mp3_bytes(w, RATE_WORD)


def word_meaning_bytes(word: str, meaning: str) -> bytes:
    parts: list[str] = []
    if word:
        parts.append(f"{word}.")
    if meaning:
        parts.append(meaning)
    return generate_mp3_bytes("  ".join(parts), RATE_MEANING)


def preview_sequence_bytes(word: str, meaning: str, example: str) -> bytes:
    """Legacy single-pass: word set (rep 1) → example, as one MP3 blob."""
    spelled = ", ".join(word.upper()) if word else ""
    parts: list[str] = []
    if intro := _PREVIEW_SETS[0][0]:
        parts.append(intro)
    if word:
        parts.append(f"{word}.")
        parts.append(f"{spelled}.")
    if meaning:
        parts.append(f"This means: {meaning}.")
    if example:
        parts.append(f"{_EXAMPLE_INTRO}  {example}")
    return generate_mp3_bytes("  ".join(parts), RATE_MEANING)


def line_bytes(text: str) -> bytes:
    """Single-line narration (used by /api/tts)."""
    return generate_mp3_bytes(text, "+0%")
