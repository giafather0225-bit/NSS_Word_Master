"""Microsoft Edge TTS — neural voices (Jenny/Aria). Much more natural than macOS say.
Requires: pip3 install edge-tts  +  internet connection.
Voice options: en-US-JennyNeural, en-US-AriaNeural, en-US-GuyNeural
Override with TTS_VOICE_EDGE env var.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import time

import edge_tts

VOICE = os.environ.get("TTS_VOICE_EDGE", "en-US-JennyNeural")

# Speech rate: "+0%" = normal, "-10%" = 10% slower, "+10%" = 10% faster
RATE_WORD    = os.environ.get("TTS_EDGE_RATE_WORD",    "-5%")
RATE_MEANING = os.environ.get("TTS_EDGE_RATE_MEANING", "-12%")
RATE_EXAMPLE = os.environ.get("TTS_EDGE_RATE_EXAMPLE", "-8%")


async def _speak_async(text: str, rate: str = "+0%") -> None:
    communicate = edge_tts.Communicate(text, VOICE, rate=rate)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        path = f.name
    try:
        await communicate.save(path)
        subprocess.run(["afplay", path], check=False)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _speak(text: str, rate: str = "+0%") -> None:
    t = (text or "").strip()
    if not t:
        return
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_speak_async(t, rate))
    finally:
        loop.close()


# Friendly phrases per repetition (0-indexed)
_PREVIEW_SETS = [
    ("",                  "This means"),
    ("Let's go again —",  "And it means"),
    ("One more time!",    "So"),
]

_EXAMPLE_INTRO = "Now let me show you this word in a real sentence."


def say_preview_word_meaning(word: str, meaning: str, rep: int = 1) -> None:
    """One study set: (optional intro) word, spelled, meaning phrase. Call 3× from frontend."""
    idx = max(0, min(rep - 1, len(_PREVIEW_SETS) - 1))
    intro, meaning_prefix = _PREVIEW_SETS[idx]

    # Build a single utterance so there's only one network round-trip
    spelled = ", ".join(word.upper()) if word else ""
    parts: list[str] = []
    if intro:
        parts.append(intro)
    if word:
        parts.append(f"{word}.")
        parts.append(f"{spelled}.")
    if meaning:
        parts.append(f"{meaning_prefix}: {meaning}.")

    _speak("  ".join(parts), RATE_MEANING)


def say_example_with_intro(example: str) -> None:
    """Example read with a friendly lead-in phrase."""
    if not (example or "").strip():
        return
    _speak(f"{_EXAMPLE_INTRO}  {example}", RATE_EXAMPLE)


def say_preview_sequence(word: str, meaning: str, example: str) -> None:
    """Legacy single-pass: word set (rep 1) → example."""
    say_preview_word_meaning(word, meaning, rep=1)
    if example:
        time.sleep(0.6)
        say_example_with_intro(example)


def say_word_then_meaning(word: str, meaning: str) -> None:
    """Training correct answer feedback."""
    if word:
        _speak(word, RATE_WORD)
        time.sleep(0.35)
    if meaning:
        _speak(meaning, RATE_MEANING)


def say_word_twice(word: str) -> None:
    """Correct answer: speak word once (fire-and-forget from typing check)."""
    w = (word or "").strip()
    if not w:
        return
    _speak(w, RATE_WORD)


def say_line(text: str) -> None:
    _speak(text)


def say_full_sentence(sentence: str) -> None:
    _speak(sentence, RATE_EXAMPLE)


# ── Browser-side playback helpers ─────────────────────────────────────────────

async def _generate_mp3_bytes(text: str, rate: str) -> bytes:
    import io
    communicate = edge_tts.Communicate(text, VOICE, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def generate_mp3_bytes(text: str, rate: str = "+0%") -> bytes:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_generate_mp3_bytes(text, rate))
    finally:
        loop.close()


def preview_word_meaning_bytes(word: str, meaning: str, rep: int = 1) -> bytes:
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
    spelled = ", ".join(word.upper()) if word else ""
    parts: list[str] = []
    if word:
        parts.append(f"{word}.")
        parts.append(f"{spelled}.")
    if meaning:
        parts.append(f"This means: {meaning}.")
    if example:
        parts.append(f"{_EXAMPLE_INTRO}  {example}")
    return generate_mp3_bytes("  ".join(parts), RATE_MEANING)
