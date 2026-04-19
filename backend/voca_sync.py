"""Voca_8000/Lesson_XX/data.json ↔ SQLite sync.

Section: English / System
Edge-case hardening (Phase 10+):
  - UPSERT by (subject, textbook, lesson, answer) — preserves StudyItem.id so
    FK references from Progress / WordAttempt / UserPracticeSentence don't break.
  - Single transaction: readers never see a "half-deleted" lesson.
  - Hard length clamps on all AI-derived text to prevent hallucination payloads
    from nuking the frontend layout or bloating SQLite.
  - Structured return with skipped-row reasons so routers can raise 422 on
    fail-open / garbage-only results.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from sqlalchemy.orm import Session

from backend.models import StudyItem

SUBJECT_DEFAULT = "vocabulary"

# Hard caps — AI hallucination defense. If a model dumps a 50k-char "definition",
# we slice. Chosen to fit the child UI (Preview card ~2 lines, modal ~5 lines).
MAX_WORD_LEN        = 120     # longest real English word is ~45 chars; be generous
MAX_DEFINITION_LEN  = 600     # one paragraph
MAX_EXAMPLE_LEN     = 400
MAX_POS_LEN         = 40
MAX_IMAGE_URL_LEN   = 1024


class SyncResult(TypedDict):
    synced: int
    skipped: int
    reasons: list[str]


def _clamp(s: str, limit: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= limit else (s[:limit].rstrip() + "…")


def _first_nonempty_text(obj: dict, keys: list[str]) -> str:
    for k in keys:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, list) and v:
            for item in v:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return ""


def lesson_json_path(voca_root: Path, lesson: str) -> Path:
    return voca_root / lesson / "data.json"


def load_lesson_json(voca_root: Path, lesson: str) -> list[dict] | None:
    p = lesson_json_path(voca_root, lesson)
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else None


def sync_lesson_to_db(
    db: Session,
    _voca_root: Path,
    lesson: str,
    rows: list[dict],
    subject: str = SUBJECT_DEFAULT,
    textbook: str = "",
    *,
    require_definition: bool = True,
) -> SyncResult:
    """UPSERT lesson rows into StudyItem within a single transaction.

    - Matches existing items by (subject, textbook, lesson, answer).
    - Updates question/hint/extra_data in place → StudyItem.id preserved.
    - Inserts new rows.
    - Deletes existing rows whose `answer` no longer appears in the new set.
    - Rows missing a definition (when require_definition=True) are skipped with
      a reason, NOT silently inserted as garbage.
    - All strings are length-clamped against AI hallucination.
    """
    # Load existing rows into memory once, keyed by answer (word).
    existing = {
        it.answer: it
        for it in db.query(StudyItem).filter(
            StudyItem.subject == subject,
            StudyItem.textbook == textbook,
            StudyItem.lesson == lesson,
        ).all()
    }

    seen: set[str] = set()
    synced = 0
    skipped = 0
    reasons: list[str] = []

    for row in rows:
        word = _clamp(row.get("word") or "", MAX_WORD_LEN)
        if not word:
            skipped += 1
            reasons.append("empty word")
            continue

        definition = _clamp(
            _first_nonempty_text(row, ["definition", "meaning", "question", "desc", "description"]),
            MAX_DEFINITION_LEN,
        )
        example = _clamp(
            _first_nonempty_text(row, ["example", "example_sentence", "examples", "sentence", "sentences"]),
            MAX_EXAMPLE_LEN,
        )

        if require_definition and not definition:
            skipped += 1
            reasons.append(f"no definition for '{word}'")
            continue

        pos = _clamp(row.get("pos") or "", MAX_POS_LEN)
        extra: dict = {"pos": pos}
        img = row.get("image_url") or row.get("image")
        if isinstance(img, str) and img.strip():
            extra["image"] = _clamp(img, MAX_IMAGE_URL_LEN)

        existing_item = existing.get(word)
        if existing_item is not None:
            # UPDATE in place — FK references to this study_item_id are preserved.
            existing_item.question   = definition
            existing_item.hint       = example
            existing_item.extra_data = json.dumps(extra, ensure_ascii=False)
        else:
            db.add(StudyItem(
                subject=subject,
                textbook=textbook,
                lesson=lesson,
                question=definition,
                answer=word,
                hint=example,
                extra_data=json.dumps(extra, ensure_ascii=False),
            ))
        seen.add(word)
        synced += 1

    # Delete rows that vanished from the new set (word no longer in textbook).
    # Single transaction → readers see old-or-new, never empty.
    for word, item in existing.items():
        if word not in seen:
            db.delete(item)

    db.commit()
    return {"synced": synced, "skipped": skipped, "reasons": reasons}
