"""
routers/words.py — Word CRUD, lesson word retrieval, and My Words routes
Section: English
Dependencies: database, models
API:
  POST   /api/words/lesson/{lesson_id}
  PATCH  /api/words/lesson/{lesson_id}/{word_id}
  DELETE /api/words/lesson/{lesson_id}/{word_id}
  GET    /api/storage/lessons/{lesson_id}/words
  POST   /api/mywords/lessons
  DELETE /api/mywords/lessons/{lesson}
  POST   /api/mywords/{lesson}/words
  DELETE /api/mywords/{lesson}/words/{word}
  PUT    /api/mywords/{lesson}/words/{word}
  PUT    /api/mywords/lessons/{lesson}/rename
  POST   /api/mywords/ai-enrich
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
from backend.models import Lesson, StudyItem, Word, GrowthEvent
from backend.schemas_common import Str20, Str100, Str500
from backend.utils import validate_lesson as _validate_lesson
from backend.services import xp_engine

router = APIRouter()
logger = logging.getLogger(__name__)

_OLLAMA_URL        = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
_OLLAMA_EVAL_MODEL = os.environ.get("OLLAMA_EVAL_MODEL", "gemma2:2b")

# ── Pydantic Schemas ───────────────────────────────────────

class ManualWordCreate(BaseModel):
    word: Str100
    definition: Str500
    example: Str500 = ""
    pos: Str20 = ""

    def clean(self):
        """No-op — length/strip enforced by Pydantic (422 on overflow)."""
        return self


class ManualWordUpdate(BaseModel):
    definition: Str500 | None = None
    example:    Str500 | None = None
    pos:        Str20  | None = None

    def clean(self):
        """No-op — length/strip enforced by Pydantic (422 on overflow)."""
        return self


# ── Helpers ────────────────────────────────────────────────

def _serialize_word(w: Word) -> dict:
    """Serialize a Word ORM row to a plain dict."""
    return {
        "id":            w.id,
        "word":          w.word,
        "pos":           w.pos,
        "definition":    w.definition,
        "example":       w.example,
        "source_type":   w.source_type,
        "study_item_id": w.study_item_id,
        "created_at":    w.created_at,
    }


# ── Routes ─────────────────────────────────────────────────

# @tag WORDS @tag MANUAL
@router.post("/api/words/lesson/{lesson_id}", status_code=201)
def create_manual_word(
    lesson_id: int,
    body: ManualWordCreate,
    db: Session = Depends(get_db),
):
    """Add a manually typed word to lesson_id (source_type='manual'); saves to words + study_items."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    req = body.clean()

    if db.query(Word).filter(Word.lesson_id == lesson_id, Word.word == req.word).first():
        raise HTTPException(
            status_code=409,
            detail=f"'{req.word}' 는 이미 lesson_id={lesson_id} 에 존재합니다.",
        )

    now = datetime.now(timezone.utc).isoformat()
    extra = json.dumps({"pos": req.pos}, ensure_ascii=False)

    study_item = StudyItem(
        subject=lesson.subject,
        textbook=lesson.textbook,
        lesson=lesson.lesson_name,
        lesson_id=lesson_id,
        source_type="manual",
        question=req.definition,
        answer=req.word,
        hint=req.example,
        extra_data=extra,
    )
    db.add(study_item)
    db.flush()

    word_obj = Word(
        word=req.word,
        definition=req.definition,
        example=req.example,
        pos=req.pos,
        lesson_id=lesson_id,
        study_item_id=study_item.id,
        source_type="manual",
        ocr_engine="",
        created_at=now,
    )
    db.add(word_obj)
    db.commit()
    db.refresh(word_obj)

    return _serialize_word(word_obj)


# @tag WORDS @tag MANUAL
@router.patch("/api/words/lesson/{lesson_id}/{word_id}")
def update_manual_word(
    lesson_id: int,
    word_id: int,
    body: ManualWordUpdate,
    db: Session = Depends(get_db),
):
    """Update definition/example/pos for a stored word and sync to study_items."""
    word_obj = db.query(Word).filter(Word.id == word_id, Word.lesson_id == lesson_id).first()
    if not word_obj:
        raise HTTPException(status_code=404, detail=f"word_id={word_id} 없음")

    req = body.clean()
    if req.definition is not None:
        word_obj.definition = req.definition
    if req.example is not None:
        word_obj.example = req.example
    if req.pos is not None:
        word_obj.pos = req.pos

    if word_obj.study_item_id:
        item = db.query(StudyItem).filter(StudyItem.id == word_obj.study_item_id).first()
        if item:
            if req.definition is not None:
                item.question = req.definition
            if req.example is not None:
                item.hint = req.example
            if req.pos is not None:
                extra = json.loads(item.extra_data or "{}")
                extra["pos"] = req.pos
                item.extra_data = json.dumps(extra, ensure_ascii=False)

    db.commit()
    db.refresh(word_obj)
    return _serialize_word(word_obj)


# @tag WORDS @tag MANUAL
@router.delete("/api/words/lesson/{lesson_id}/{word_id}", status_code=204)
def delete_manual_word(
    lesson_id: int,
    word_id: int,
    db: Session = Depends(get_db),
):
    """Delete a word (and its linked study_item) from a lesson."""
    word_obj = db.query(Word).filter(Word.id == word_id, Word.lesson_id == lesson_id).first()
    if not word_obj:
        raise HTTPException(status_code=404, detail=f"word_id={word_id} 없음")

    if word_obj.study_item_id:
        item = db.query(StudyItem).filter(StudyItem.id == word_obj.study_item_id).first()
        if item:
            db.delete(item)

    db.delete(word_obj)
    db.commit()


# @tag WORDS @tag STORAGE
@router.get("/api/storage/lessons/{lesson_id}/words")
def get_lesson_words(lesson_id: int, db: Session = Depends(get_db)):
    """Return all words stored in the words table for a given lesson_id."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson id={lesson_id} 없음")

    words = (
        db.query(Word)
        .filter(Word.lesson_id == lesson_id)
        .order_by(Word.id)
        .all()
    )
    return {
        "lesson_id":   lesson_id,
        "lesson_name": lesson.lesson_name,
        "words": [
            {
                "id":           w.id,
                "word":         w.word,
                "pos":          w.pos,
                "definition":   w.definition,
                "example":      w.example,
                "ocr_engine":   w.ocr_engine,
                "study_item_id": w.study_item_id,
                "created_at":   w.created_at,
            }
            for w in words
        ],
        "count": len(words),
    }


# ── My Words routes ────────────────────────────────────────

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
    shutil.rmtree(lesson_dir)
    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
    ).delete()
    db.commit()
    return {"deleted": safe}


# @tag WORDS @tag MYWORDS
@router.post("/api/mywords/{lesson}/words")
def add_myword(lesson: str, body: dict, db: Session = Depends(get_db)):
    """Add a word to a My_Words lesson; syncs data.json and DB."""
    safe = _validate_lesson(lesson)
    lesson_dir = LEARNING_ROOT / "English" / "My_Words" / safe
    if not lesson_dir.exists():
        raise HTTPException(404, "Lesson not found")

    word       = body.get("word", "").strip()
    definition = body.get("definition", "").strip()
    example    = body.get("example", "").strip()
    pos        = body.get("pos", "").strip()

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

    json_path.write_text(json.dumps(new_items, indent=2, ensure_ascii=False), encoding="utf-8")

    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
        StudyItem.answer == word,
    ).delete()
    db.commit()
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

    items = json.loads(json_path.read_text(encoding="utf-8"))
    found = False
    for it in items:
        if it["word"].lower() == word.lower():
            if body.get("definition"):
                it["definition"] = body["definition"]
            if body.get("example"):
                it["example"] = body["example"]
            if body.get("pos"):
                it["pos"] = body["pos"]
            found = True
            break
    if not found:
        raise HTTPException(404, f"Word '{word}' not found")

    json_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    row = db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == safe,
        StudyItem.answer == word,
    ).first()
    if row:
        if body.get("definition"):
            row.question = body["definition"]
        if body.get("example"):
            row.hint = (
                body["example"].replace(word, "____")
                if word in body["example"]
                else body["example"]
            )
        if body.get("pos"):
            extra = json.loads(row.extra_data or "{}")
            extra["pos"] = body["pos"]
            row.extra_data = json.dumps(extra)
        db.commit()

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

    old_dir.rename(new_dir)

    db.query(StudyItem).filter(
        StudyItem.subject == "English",
        StudyItem.textbook == "My_Words",
        StudyItem.lesson == old_safe,
    ).update({"lesson": new_name})
    db.commit()

    return {"old": old_safe, "new": new_name}


# @tag WORDS @tag MYWORDS @tag AI
@router.post("/api/mywords/ai-enrich")
async def ai_enrich_word(body: dict):
    """Use Ollama (or fallback template) to generate a kid-friendly definition + example."""
    word = body.get("word", "").strip()
    pos  = body.get("pos", "").strip()
    if not word:
        raise HTTPException(400, "Word is required")

    prompt = f"""You are a friendly English teacher for a 10-year-old Korean student.
For the word "{word}" ({pos if pos else 'any part of speech'}):
1. Write a simple, clear definition (1 sentence, easy words)
2. Write a fun, relatable example sentence using the word

Reply in this exact JSON format only:
{{"definition": "...", "example": "...", "pos": "{pos if pos else '...'}"}}"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{_OLLAMA_URL}/api/generate", json={
                "model": _OLLAMA_EVAL_MODEL,
                "prompt": prompt,
                "stream": False,
            })
            if r.status_code == 200:
                text = r.json().get("response", "")
                m = _re.search(r'\{[^}]+\}', text)
                if m:
                    result = json.loads(m.group())
                    result["provider"] = "ollama"
                    return result
    except Exception as e:
        logger.warning("Ollama failed: %s", e)

    return {
        "definition": "",
        "example": "",
        "pos": pos,
        "provider": "manual",
    }


# ── My Words Weekly Test ───────────────────────────────────

MYWORDS_TEST_MIN_WORDS = 50
MYWORDS_TEST_SIZE = 20
MYWORDS_TEST_PASS_PCT = 0.9


class MyWordsTestResult(BaseModel):
    correct_count: int
    total_count: int


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
        xp_awarded = xp_engine.award_xp(db, "mywords_weekly_test_pass", "my_words")
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
