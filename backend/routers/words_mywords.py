"""
words_mywords.py — My Words CRUD, AI enrich, and weekly test routes
Section: English
Dependencies: database, models, services/xp_engine
API:
  POST   /api/mywords/lessons
  DELETE /api/mywords/lessons/{lesson}
  POST   /api/mywords/{lesson}/words
  DELETE /api/mywords/{lesson}/words/{word}
  PUT    /api/mywords/{lesson}/words/{word}
  PUT    /api/mywords/lessons/{lesson}/rename
  POST   /api/mywords/ai-enrich
  GET    /api/mywords/weekly-test
  POST   /api/mywords/weekly-test/result
"""
import json
import logging
import os
import random
import re as _re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db, LEARNING_ROOT
from backend.models import StudyItem, GrowthEvent
from backend.utils import validate_lesson as _validate_lesson, parse_json_array as _parse_json_array
from backend.services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_OLLAMA_URL        = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_OLLAMA_EVAL_MODEL = os.environ.get("OLLAMA_EVAL_MODEL", "gemma2:2b")

MYWORDS_TEST_MIN_WORDS = 50
MYWORDS_TEST_SIZE = 20
MYWORDS_TEST_PASS_PCT = 0.9


class MyWordsTestResult(BaseModel):
    correct_count: int
    total_count: int


# @tag WORDS @tag MYWORDS
@router.post("/api/mywords/lessons")
def create_mywords_lesson(body: dict, db: Session = Depends(get_db)):
    """Create a new lesson under English/My_Words/."""
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Lesson name required")
    safe = _validate_lesson(name)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    if lesson_dir.exists():
        raise HTTPException(409, f"Lesson '{safe}' already exists")
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "data.json").write_text("[]", encoding="utf-8")
    return {"lesson": safe, "path": str(lesson_dir)}


# @tag WORDS @tag MYWORDS
@router.delete("/api/mywords/lessons/{lesson}")
def delete_mywords_lesson(lesson: str, db: Session = Depends(get_db)):
    """Delete a My_Words lesson folder and its DB records."""
    safe = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    if not lesson_dir.exists():
        raise HTTPException(404, "Lesson not found")
    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
    ).delete()
    db.commit()
    try:
        shutil.rmtree(lesson_dir)
    except OSError as e:
        logger.error("delete_mywords_lesson: rmtree failed for %s: %s", safe, e)
    return {"deleted": safe}


# @tag WORDS @tag MYWORDS
@router.post("/api/mywords/{lesson}/words")
def add_myword(lesson: str, body: dict, db: Session = Depends(get_db)):
    """Add a word to a My_Words lesson; syncs data.json and DB."""
    safe = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    if not lesson_dir.exists():
        raise HTTPException(404, "Lesson not found")

    word       = (body.get("word", "") or "").strip()[:100]
    definition = (body.get("definition", "") or "").strip()[:500]
    example    = (body.get("example", "") or "").strip()[:500]
    pos        = (body.get("pos", "") or "").strip()[:20]

    if not word:
        raise HTTPException(400, "Word is required")

    json_path = lesson_dir / "data.json"
    items = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else []

    if any(it["word"].lower() == word.lower() for it in items):
        raise HTTPException(409, f"Word '{word}' already exists")

    entry = {"word": word, "pos": pos, "definition": definition, "example": example}
    items.append(entry)
    json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    hint = example.replace(word, "____") if word in example else example
    item = StudyItem(
        subject="English", textbook="My_Words", lesson=safe,
        question=definition, answer=word, hint=hint,
        extra_data=json.dumps({"pos": pos, "source": "manual"}),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {"id": item.id, "word": word, "definition": definition, "example": example, "pos": pos}


# @tag WORDS @tag MYWORDS
@router.delete("/api/mywords/{lesson}/words/{word}")
def delete_myword(lesson: str, word: str, db: Session = Depends(get_db)):
    """Delete a word from a My_Words lesson (data.json + DB)."""
    safe = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    json_path = lesson_dir / "data.json"

    if not json_path.exists():
        raise HTTPException(404, "Lesson not found")

    items = json.loads(json_path.read_text(encoding="utf-8"))
    new_items = [it for it in items if it["word"].lower() != word.lower()]
    if len(new_items) == len(items):
        raise HTTPException(404, f"Word '{word}' not found")

    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
        StudyItem.answer == word,
    ).delete()
    db.commit()
    try:
        json_path.write_text(json.dumps(new_items, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        logger.error("delete_myword: write_text failed for %s/%s: %s", safe, word, e)
    return {"deleted": word}


# @tag WORDS @tag MYWORDS
@router.put("/api/mywords/{lesson}/words/{word}")
def update_myword(lesson: str, word: str, body: dict, db: Session = Depends(get_db)):
    """Update a word's definition/example/pos in a My_Words lesson."""
    safe = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    json_path = lesson_dir / "data.json"

    if not json_path.exists():
        raise HTTPException(404, "Lesson not found")

    new_def = (body.get("definition") or "").strip()[:500] or None
    new_ex  = (body.get("example") or "").strip()[:500] or None
    new_pos = (body.get("pos") or "").strip()[:20] or None

    items = json.loads(json_path.read_text(encoding="utf-8"))
    found = False
    for it in items:
        if it["word"].lower() == word.lower():
            if new_def: it["definition"] = new_def
            if new_ex:  it["example"]    = new_ex
            if new_pos: it["pos"]        = new_pos
            found = True
            break
    if not found:
        raise HTTPException(404, f"Word '{word}' not found")

    row = db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
        StudyItem.answer == word,
    ).first()
    if row:
        if new_def: row.question = new_def
        if new_ex:  row.hint = new_ex.replace(word, "____") if word in new_ex else new_ex
        if new_pos:
            extra = json.loads(row.extra_data or "{}")
            extra["pos"] = new_pos
            row.extra_data = json.dumps(extra)
        db.commit()
    try:
        json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        logger.error("update_myword: write_text failed for %s/%s: %s", safe, word, e)

    return {"updated": word}


# @tag WORDS @tag MYWORDS
@router.put("/api/mywords/lessons/{lesson}/rename")
def rename_mywords_lesson(lesson: str, body: dict, db: Session = Depends(get_db)):
    """Rename a My_Words lesson folder and update all DB records."""
    old_safe = _validate_lesson(lesson)
    raw_new = body.get("name", "").strip()
    if not raw_new:
        raise HTTPException(400, "New name required")
    new_name = _validate_lesson(raw_new)

    old_dir = LEARNING_ROOT / "English" / "My_Words" / old_safe
    new_dir = LEARNING_ROOT / "English" / "My_Words" / new_name

    if not old_dir.exists():
        raise HTTPException(404, "Lesson not found")
    if new_dir.exists() and old_safe != new_name:
        raise HTTPException(409, f"Lesson '{new_name}' already exists")

    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == old_safe,
    ).update({"lesson": new_name})
    db.commit()
    try:
        old_dir.rename(new_dir)
    except OSError as e:
        logger.error("rename_mywords_lesson: rename failed %s→%s: %s", old_safe, new_name, e)

    return {"old": old_safe, "new": new_name}


# @tag WORDS @tag MYWORDS @tag AI
@router.post("/api/mywords/ai-enrich")
async def ai_enrich_word(body: dict):
    """Use Ollama (or fallback template) to generate a kid-friendly definition + example."""
    import re as _re
    word = body.get("word", "").strip()[:80]
    pos  = body.get("pos", "").strip()[:40]
    if not word:
        raise HTTPException(400, "Word is required")
    # Strip any prompt-injection attempts (quotes, braces, newlines)
    word_safe = _re.sub(r'["\n\r{}\\]', '', word)
    pos_safe  = _re.sub(r'["\n\r{}\\]', '', pos) if pos else ""

    prompt = f"""You are a friendly English teacher for a 10-year-old Korean student.
For the word "{word_safe}" ({pos_safe if pos_safe else 'any part of speech'}):
1. Write a simple, clear definition (1 sentence, easy words)
2. Write a fun, relatable example sentence using the word

Reply in this exact JSON format only:
{{"definition": "...", "example": "...", "pos": "{pos_safe if pos_safe else '...'}"}}"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{_OLLAMA_URL}/api/generate", json={
                "model": _OLLAMA_EVAL_MODEL,
                "prompt": prompt,
                "stream": False,
            })
            if r.status_code == 200:
                text = r.json().get("response", "")
                result = _parse_json_array(text)
                if result and isinstance(result, list) and result[0]:
                    result[0]["provider"] = "ollama"
                    return result[0]
                import json as _json2
                try:
                    obj = _json2.loads(text.strip())
                    if isinstance(obj, dict) and obj.get("definition"):
                        obj["provider"] = "ollama"
                        return obj
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Ollama failed: %s", e)

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            gemini_url = (
                "https://generativelanguage.googleapis.com/v1/models/"
                "gemini-2.0-flash:generateContent"
            )
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    gemini_url,
                    json={"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"temperature": 0.3, "maxOutputTokens": 256}},
                    headers={"x-goog-api-key": gemini_key},
                )
                if r.status_code == 200:
                    text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    import json as _json2
                    result = _parse_json_array(text)
                    if result and isinstance(result, list) and result[0]:
                        result[0]["provider"] = "gemini"
                        return result[0]
                    try:
                        obj = _json2.loads(text)
                        if isinstance(obj, dict) and obj.get("definition"):
                            obj["provider"] = "gemini"
                            return obj
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Gemini fallback failed: %s", e)

    return {
        "definition": "",
        "example": "",
        "pos": pos,
        "provider": "manual",
    }


# @tag WORDS @tag MYWORDS @tag WEEKLY_TEST
@router.get("/api/mywords/weekly-test")
def mywords_weekly_test(db: Session = Depends(get_db)):
    """Return a sampled weekly test set drawn from all My_Words lessons.

    Gate: caller must have at least MYWORDS_TEST_MIN_WORDS words stored across
    all My_Words lessons combined. If the gate isn't met, returns
    ``{available: False, total_word_count, min_required}`` instead of a 400 so
    the UI can show a friendly "add more words" state.
    """
    pool = (
        db.query(StudyItem)
        .filter(
            StudyItem.subject == "English",
            StudyItem.textbook == "My_Words",
        )
        .all()
    )
    total = len(pool)
    if total < MYWORDS_TEST_MIN_WORDS:
        return {
            "available": False,
            "total_word_count": total,
            "min_required": MYWORDS_TEST_MIN_WORDS,
            "test_size": MYWORDS_TEST_SIZE,
            "words": [],
        }

    sample = random.sample(pool, min(MYWORDS_TEST_SIZE, total))
    words = []
    for it in sample:
        try:
            extra = json.loads(it.extra_data or "{}")
        except Exception:
            extra = {}
        words.append({
            "id":         it.id,
            "word":       it.answer or "",
            "definition": it.question or "",
            "example":    it.hint or "",
            "pos":        extra.get("pos", ""),
            "lesson":     it.lesson,
        })

    return {
        "available": True,
        "total_word_count": total,
        "min_required": MYWORDS_TEST_MIN_WORDS,
        "test_size": len(words),
        "pass_pct": MYWORDS_TEST_PASS_PCT,
        "words": words,
    }


# @tag WORDS @tag MYWORDS @tag WEEKLY_TEST @tag XP
@router.post("/api/mywords/weekly-test/result")
def mywords_weekly_test_result(
    body: MyWordsTestResult, db: Session = Depends(get_db)
):
    """Record a My Words weekly test result. Award XP +10 on pass (≥90%)."""
    if body.total_count <= 0:
        raise HTTPException(400, "total_count must be > 0")
    if body.correct_count < 0 or body.correct_count > body.total_count:
        raise HTTPException(400, "correct_count out of range")

    accuracy = body.correct_count / body.total_count
    passed = accuracy >= MYWORDS_TEST_PASS_PCT
    xp_awarded = 0

    if passed:
        xp_awarded = xp_engine.award_xp(db, "mywords_weekly_test_pass", "my_words", commit=False)
        if xp_awarded > 0:
            now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
            today_iso = date.today().isoformat()
            db.add(GrowthEvent(
                event_type="weekly_test_pass",
                title="My Words weekly test passed",
                detail=f"{body.correct_count}/{body.total_count} ({int(accuracy*100)}%)",
                event_date=today_iso,
                created_at=now_iso,
            ))
            db.commit()

    return {
        "ok": True,
        "passed": passed,
        "accuracy": round(accuracy, 3),
        "xp_awarded": xp_awarded,
    }
