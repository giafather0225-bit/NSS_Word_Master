"""Mac built-in TTS (`say`). 기본 Samantha — Siri 품질에 가까운 EN-US. 다른 목소리: TTS_VOICE 환경변수 (예: Karen, Moira). `say -v '?'` 로 전체 목록."""
from __future__ import annotations

import os
import subprocess
import time

TTS_VOICE = os.environ.get("TTS_VOICE", "Samantha")

# wpm rates — natural, warm pacing for learners
RATE_WORD    = int(os.environ.get("TTS_RATE_WORD",    "148"))
RATE_MEANING = int(os.environ.get("TTS_RATE_MEANING", "130"))
RATE_EXAMPLE = int(os.environ.get("TTS_RATE_EXAMPLE", "138"))

PAUSE_SET_SEC          = 0.55  # pause between word and meaning inside one set
PAUSE_BETWEEN_SETS_SEC = 1.0   # pause between repeated sets
PAUSE_BEFORE_EXAMPLE   = 1.2

# Embedded prosody — warmer pitch and more natural modulation
# [[pbas 52]] raises pitch slightly (friendlier); [[pmod 60]] adds tonal variation
_PROSODY = "[[pbas 52]][[pmod 60]]"


def _say(text: str, rate: int | None = None) -> None:
    t = (text or "").strip()
    if not t:
        return
    cmd = ["say", "-v", TTS_VOICE]
    if rate:
        cmd += ["-r", str(rate)]
    cmd.append(_PROSODY + t)
    subprocess.run(cmd, check=False)


def say_preview_sequence(word: str, meaning: str, example: str) -> None:
    """Legacy: word → meaning → example (single pass)."""
    if word:   _say(word,    RATE_WORD)
    time.sleep(PAUSE_SET_SEC)
    if meaning: _say(meaning, RATE_MEANING)
    time.sleep(PAUSE_BEFORE_EXAMPLE)
    if example: _say(example, RATE_EXAMPLE)


def say_preview_word_meaning(word: str, meaning: str, rep: int = 1) -> None:
    """Preview set: word (normal) → brief pause → meaning (slow).
    Called 3× from frontend for spaced repetition. rep param accepted for API compat."""
    if word:    _say(word,    RATE_WORD)
    time.sleep(PAUSE_SET_SEC)
    if meaning: _say(meaning, RATE_MEANING)


def say_word_then_meaning(word: str, meaning: str) -> None:
    """Training correct answer: word → short pause → meaning."""
    if word:    _say(word,    RATE_WORD)
    time.sleep(0.4)
    if meaning: _say(meaning, RATE_MEANING)


def say_line(text: str) -> None:
    _say(text)


def say_word_twice(word: str) -> None:
    """Spelling Master: word spoken twice."""
    w = (word or "").strip()
    if not w:
        return
    _say(w, RATE_WORD)
    time.sleep(0.35)
    _say(w, RATE_WORD)


def say_full_sentence(sentence: str) -> None:
    _say(sentence, RATE_EXAMPLE)
