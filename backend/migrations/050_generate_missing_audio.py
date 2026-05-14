"""
Migration 050 — Generate edge-tts MP3s for CKLA G3 words with no audio_url
===========================================================================
62 words across all 11 domains are missing audio (MW/Free Dictionary API
has no entry for compound words and multi-word phrases like "mammary glands",
"energy pyramid", "invasive species", etc.).

This migration:
  1. Generates edge-tts MP3 (en-US-JennyNeural, -5% rate) for every G3 word
     whose audio_url is NULL or ''.
  2. Saves the file to  frontend/static/audio/ckla/<word_id>.mp3
  3. Updates us_academy_words.audio_url = '/static/audio/ckla/<word_id>.mp3'

Idempotent: skips words that already have audio_url set OR whose .mp3 file
already exists on disk.

Run:
    python3 backend/migrations/050_generate_missing_audio.py
"""

import asyncio
import io
import sqlite3
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
DB_PATH     = Path.home() / "NSS_Learning" / "database" / "voca.db"
REPO_ROOT   = Path(__file__).resolve().parents[2]          # NSS_Word_Master/
AUDIO_DIR   = REPO_ROOT / "frontend" / "static" / "audio" / "ckla"
STATIC_BASE = "/static/audio/ckla"                         # URL prefix

# ── TTS settings ──────────────────────────────────────────────────────────────
VOICE = "en-US-JennyNeural"
RATE  = "-5%"


async def _generate_mp3(text: str) -> bytes:
    """Return raw MP3 bytes for text via edge-tts."""
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError("edge-tts not installed. Run: pip3 install edge-tts")

    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    mp3 = buf.getvalue()
    if not mp3:
        raise ValueError(f"edge-tts returned empty audio for: {text!r}")
    return mp3


def run(db_path: str = str(DB_PATH)) -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # Fetch all G3 words missing audio (de-duped by word_id)
    cur.execute("""
        SELECT DISTINCT w.id, w.word
        FROM us_academy_lessons l
        JOIN us_academy_word_lesson wl ON wl.lesson_id = l.id
        JOIN us_academy_words w ON w.id = wl.word_id
        WHERE l.grade = 3
          AND (w.audio_url IS NULL OR w.audio_url = '')
        ORDER BY w.id
    """)
    rows = cur.fetchall()

    if not rows:
        print("[050] Nothing to do — all G3 words already have audio_url.")
        conn.close()
        return

    print(f"[050] {len(rows)} words to process...")

    ok = skip = fail = 0
    loop = asyncio.new_event_loop()

    for word_id, word in rows:
        mp3_path = AUDIO_DIR / f"{word_id}.mp3"
        url      = f"{STATIC_BASE}/{word_id}.mp3"

        # File already exists → just update DB if needed
        if mp3_path.exists():
            cur.execute(
                "UPDATE us_academy_words SET audio_url=? WHERE id=? AND (audio_url IS NULL OR audio_url='')",
                (url, word_id),
            )
            skip += 1
            continue

        # Generate MP3
        try:
            mp3_bytes = loop.run_until_complete(_generate_mp3(word))
        except Exception as exc:
            print(f"  [FAIL] id={word_id} {word!r}: {exc}")
            fail += 1
            continue

        mp3_path.write_bytes(mp3_bytes)
        cur.execute(
            "UPDATE us_academy_words SET audio_url=? WHERE id=?",
            (url, word_id),
        )
        ok += 1
        print(f"  [OK]   id={word_id:4d}  {word}")

    loop.close()
    conn.commit()
    conn.close()

    print(f"\n[050] Done — generated {ok}, skipped {skip} (already existed), failed {fail}.")
    if fail:
        print(f"[050] Warning: {fail} audio files could not be generated (TTS unavailable at startup).")


if __name__ == "__main__":
    run()
