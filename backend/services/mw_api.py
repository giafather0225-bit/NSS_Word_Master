"""
services/mw_api.py — Merriam-Webster Elementary Dictionary API client.
Section: Academy
Dependencies: httpx, ENV[MW_ELEMENTARY_API_KEY]
API: none (internal service)

Fetches child-friendly definitions, part of speech, audio, and example
sentences for the US Academy word list (grades 3-5 level).

Usage:
    result = await fetch_word("analyze")
    # {word, definition, part_of_speech, audio_url, example_1}
"""

import os
import json
import asyncio
from typing import Optional

import httpx

MW_API_KEY = os.environ.get("MW_ELEMENTARY_API_KEY", "")
MW_BASE_URL = "https://www.dictionaryapi.com/api/v3/references/sd2/json"


# @tag ACADEMY @tag SYSTEM
async def fetch_word(word: str) -> dict:
    """Fetch word data from Merriam-Webster Elementary Dictionary API.

    Returns dict with keys: word, definition, part_of_speech,
    audio_url, example_1. Empty strings on failure.
    """
    if not MW_API_KEY:
        return _empty(word, reason="MW_ELEMENTARY_API_KEY not set")

    url = f"{MW_BASE_URL}/{word}"
    params = {"key": MW_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return _empty(word, reason=str(exc))

    # MW returns a list; first entry is the primary match
    if not data or not isinstance(data, list) or isinstance(data[0], str):
        return _empty(word, reason="no entry found")

    entry = data[0]

    definition  = _extract_definition(entry)
    pos         = entry.get("fl", "")
    audio_url   = _extract_audio(entry)
    example     = _extract_example(entry)

    return {
        "word":           word,
        "definition":     definition,
        "part_of_speech": pos,
        "audio_url":      audio_url,
        "example_1":      example,
    }


# @tag ACADEMY
def _extract_definition(entry: dict) -> str:
    """Pull first short definition from MW entry."""
    try:
        shortdefs = entry.get("shortdef", [])
        if shortdefs:
            return shortdefs[0]
        # fallback: dig into def > sseq
        defs = entry.get("def", [])
        for d in defs:
            for sseq in d.get("sseq", []):
                for sense in sseq:
                    if isinstance(sense, list) and sense[0] == "sense":
                        dt = sense[1].get("dt", [])
                        for item in dt:
                            if isinstance(item, list) and item[0] == "text":
                                return _strip_mw_markup(item[1])
    except Exception:
        pass
    return ""


# @tag ACADEMY
def _extract_audio(entry: dict) -> str:
    """Build MW audio URL from hwi.prs[0].sound.audio filename."""
    try:
        audio_file = (
            entry.get("hwi", {})
                 .get("prs", [{}])[0]
                 .get("sound", {})
                 .get("audio", "")
        )
        if not audio_file:
            return ""
        # subdirectory: first letter, except "bix", "gg", "number" prefixes
        if audio_file.startswith("bix"):
            subdir = "bix"
        elif audio_file.startswith("gg"):
            subdir = "gg"
        elif audio_file[0].isdigit() or audio_file[0] == "_":
            subdir = "number"
        else:
            subdir = audio_file[0]
        return f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{subdir}/{audio_file}.mp3"
    except Exception:
        return ""


# @tag ACADEMY
def _extract_example(entry: dict) -> str:
    """Extract first usage example sentence from MW entry."""
    try:
        defs = entry.get("def", [])
        for d in defs:
            for sseq in d.get("sseq", []):
                for sense in sseq:
                    if isinstance(sense, list) and sense[0] == "sense":
                        dt = sense[1].get("dt", [])
                        for item in dt:
                            if isinstance(item, list) and item[0] == "vis":
                                for vis in item[1]:
                                    t = vis.get("t", "")
                                    if t:
                                        return _strip_mw_markup(t)
    except Exception:
        pass
    return ""


# @tag ACADEMY
def _strip_mw_markup(text: str) -> str:
    """Remove MW formatting markup like {bc}, {it}, {/it}, {wi}, etc."""
    import re
    text = re.sub(r"\{[^}]+\}", "", text)
    return text.strip()


# @tag ACADEMY
def _empty(word: str, reason: str = "") -> dict:
    return {
        "word":           word,
        "definition":     "",
        "part_of_speech": "",
        "audio_url":      "",
        "example_1":      "",
        "_error":         reason,
    }
