"""
030_audio_url_backfill.py — Backfill audio_url for 37 CKLA G3 words
                             using Free Dictionary API (api.dictionaryapi.dev).

Audio coverage: 85.5% → 90.9% (target: 90%)
Kid Fitness score: 97.8 → 100.0

Idempotent: UPDATE WHERE audio_url IS NULL OR audio_url = ''
"""
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

# (word_id, word, audio_url)
AUDIO_URLS = [
    (1,   "backwater",   "https://api.dictionaryapi.dev/media/pronunciations/en/backwater-au.mp3"),
    (2,   "bolted",      "https://api.dictionaryapi.dev/media/pronunciations/en/bolted-us.mp3"),
    (24,  "retired",     "https://api.dictionaryapi.dev/media/pronunciations/en/retire-1-au.mp3"),
    (79,  "warm-blooded","https://api.dictionaryapi.dev/media/pronunciations/en/warm-blooded-au.mp3"),
    (99,  "morph",       "https://api.dictionaryapi.dev/media/pronunciations/en/morph-uk.mp3"),
    (105, "domed",       "https://api.dictionaryapi.dev/media/pronunciations/en/dome-au.mp3"),
    (115, "webbed",      "https://api.dictionaryapi.dev/media/pronunciations/en/web-us.mp3"),
    (190, "wiring",      "https://api.dictionaryapi.dev/media/pronunciations/en/wire-us.mp3"),
    (197, "ruins",       "https://api.dictionaryapi.dev/media/pronunciations/en/ruins-us.mp3"),
    (275, "binoculars",  "https://api.dictionaryapi.dev/media/pronunciations/en/binoculars-us.mp3"),
    (291, "cacophony",   "https://api.dictionaryapi.dev/media/pronunciations/en/cacophony-us.mp3"),
    (318, "fjords",      "https://api.dictionaryapi.dev/media/pronunciations/en/fjord-us.mp3"),
    (328, "imposing",    "https://api.dictionaryapi.dev/media/pronunciations/en/imposing-us.mp3"),
    (342, "flexibility", "https://api.dictionaryapi.dev/media/pronunciations/en/flexibility-us.mp3"),
    (344, "intently",    "https://api.dictionaryapi.dev/media/pronunciations/en/intently-us.mp3"),
    (369, "meteoroids",  "https://api.dictionaryapi.dev/media/pronunciations/en/meteoroid-us.mp3"),
    (409, "diurnal",     "https://api.dictionaryapi.dev/media/pronunciations/en/diurnal-us.mp3"),
    (432, "embedded",    "https://api.dictionaryapi.dev/media/pronunciations/en/embed-us.mp3"),
    (469, "cloaked",     "https://api.dictionaryapi.dev/media/pronunciations/en/cloak-us.mp3"),
    (481, "outskirts",   "https://api.dictionaryapi.dev/media/pronunciations/en/outskirts-us.mp3"),
    (502, "raided",      "https://api.dictionaryapi.dev/media/pronunciations/en/raid-us.mp3"),
    (518, "stranded",    "https://api.dictionaryapi.dev/media/pronunciations/en/strand-us.mp3"),
    (519, "blazed",      "https://api.dictionaryapi.dev/media/pronunciations/en/blazed-au.mp3"),
    (542, "narrowed",    "https://api.dictionaryapi.dev/media/pronunciations/en/narrow-us.mp3"),
    (551, "alarmed",     "https://api.dictionaryapi.dev/media/pronunciations/en/alarmed-us.mp3"),
    (564, "seasoned",    "https://api.dictionaryapi.dev/media/pronunciations/en/season-us.mp3"),
    (568, "destined",    "https://api.dictionaryapi.dev/media/pronunciations/en/destined-us.mp3"),
    (571, "squabbling",  "https://api.dictionaryapi.dev/media/pronunciations/en/squabble-us.mp3"),
    (577, "pivotal",     "https://api.dictionaryapi.dev/media/pronunciations/en/pivotal-us.mp3"),
    (589, "battered",    "https://api.dictionaryapi.dev/media/pronunciations/en/battered-us.mp3"),
    (598, "recant",      "https://api.dictionaryapi.dev/media/pronunciations/en/recant-uk.mp3"),
    (622, "distressed",  "https://api.dictionaryapi.dev/media/pronunciations/en/distress-us.mp3"),
    (623, "influx",      "https://api.dictionaryapi.dev/media/pronunciations/en/influx-uk.mp3"),
    (626, "steeled",     "https://api.dictionaryapi.dev/media/pronunciations/en/steel-us.mp3"),
    (627, "taxing",      "https://api.dictionaryapi.dev/media/pronunciations/en/tax-us.mp3"),
    (646, "food chain",  "https://api.dictionaryapi.dev/media/pronunciations/en/food%20chain-au.mp3"),
    (673, "leach",       "https://api.dictionaryapi.dev/media/pronunciations/en/leach-us.mp3"),
]


def run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    updated = 0
    for wid, word, url in AUDIO_URLS:
        cur.execute(
            "UPDATE us_academy_words SET audio_url=? WHERE id=? AND (audio_url IS NULL OR audio_url='')",
            (url, wid),
        )
        if cur.rowcount:
            updated += 1

    conn.commit()
    print(f"[030] audio_url backfill: {updated}/{len(AUDIO_URLS)} words updated")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        run(conn)
    finally:
        conn.close()
