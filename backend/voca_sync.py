"""Voca_8000/Lesson_XX/data.json ↔ SQLite 동기화."""
from __future__ import annotations

import json
from pathlib import Path
from sqlalchemy.orm import Session

from backend.models import StudyItem

SUBJECT_DEFAULT = "vocabulary"


def _first_nonempty_text(obj: dict, keys: list[str]) -> str:
    for k in keys:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, list) and v:
            # If model returns multiple examples/definitions, keep the first non-empty.
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
) -> int:
    db.query(StudyItem).filter(
        StudyItem.subject == subject,
        StudyItem.textbook == textbook,
        StudyItem.lesson == lesson,
    ).delete(synchronize_session=False)

    count = 0
    for row in rows:
        w = (row.get("word") or "").strip()
        if not w:
            continue
        extra = {"pos": row.get("pos") or ""}
        if row.get("image_url"):
            extra["image"] = row["image_url"]
        if row.get("image"):
            extra["image"] = row["image"]
        db.add(
            StudyItem(
                subject=subject,
                textbook=textbook,
                lesson=lesson,
                question=_first_nonempty_text(
                    row,
                    [
                        "definition",
                        "meaning",
                        "question",
                        "desc",
                        "description",
                    ],
                ),
                answer=w,
                hint=_first_nonempty_text(
                    row,
                    [
                        "example",
                        "example_sentence",
                        "examples",
                        "sentence",
                        "sentences",
                    ],
                ),
                extra_data=json.dumps(extra, ensure_ascii=False),
            )
        )
        count += 1
    db.commit()
    return count
