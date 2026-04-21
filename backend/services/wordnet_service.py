"""
services/wordnet_service.py — Princeton WordNet synonym/antonym lookup.
Section: Academy
Dependencies: nltk, nltk.corpus.wordnet
API: none (internal service)

Returns top synonyms and antonyms for a given word using WordNet.
NLTK wordnet data is auto-downloaded on first use.

Usage:
    result = get_synonyms_antonyms("analyze")
    # {"synonyms": ["examine", "study", ...], "antonyms": [...]}
"""

import json
from typing import Optional


# @tag ACADEMY
def _ensure_wordnet() -> bool:
    """Download wordnet data if not present. Returns True on success."""
    try:
        import nltk
        try:
            from nltk.corpus import wordnet as wn
            wn.synsets("test")  # trigger download check
        except LookupError:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
        return True
    except ImportError:
        return False


# @tag ACADEMY
def get_synonyms_antonyms(word: str, max_each: int = 5) -> dict:
    """Return synonyms and antonyms for a word via WordNet.

    Returns {"synonyms": [...], "antonyms": [...]}
    Both lists may be empty if WordNet has no data for the word.
    """
    if not _ensure_wordnet():
        return {"synonyms": [], "antonyms": [], "_error": "nltk not installed"}

    from nltk.corpus import wordnet as wn

    synonyms: set[str] = set()
    antonyms: set[str] = set()

    for synset in wn.synsets(word):
        for lemma in synset.lemmas():
            name = lemma.name().replace("_", " ")
            if name.lower() != word.lower():
                synonyms.add(name)
            for ant in lemma.antonyms():
                antonyms.add(ant.name().replace("_", " "))

    # filter: single words only, no duplicates, max count
    syn_list = sorted(s for s in synonyms if " " not in s)[:max_each]
    ant_list = sorted(a for a in antonyms if " " not in a)[:max_each]

    return {"synonyms": syn_list, "antonyms": ant_list}


# @tag ACADEMY
def get_synonyms_antonyms_json(word: str, max_each: int = 5) -> tuple[str, str]:
    """Return (synonyms_json, antonyms_json) as JSON strings for DB storage."""
    result = get_synonyms_antonyms(word, max_each)
    return (
        json.dumps(result["synonyms"]),
        json.dumps(result["antonyms"]),
    )
