"""
routers/diary_sentences.py — Diary "My Sentences" view.
Section: Diary
Dependencies: models.py (UserPracticeSentence, StudyItem)
API: GET /api/diary/{subject}/{textbook}

Catch-all path; MUST be registered AFTER routers/diary_photo.py in main.py
so the literal `/api/diary/photo/...` route wins matching.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import UserPracticeSentence, StudyItem
except ImportError:
    from database import get_db
    from models import UserPracticeSentence, StudyItem

router = APIRouter()


# @tag DIARY @tag MY_SENTENCES
@router.get("/api/diary/{subject}/{textbook}")
def get_diary_sentences(subject: str, textbook: str, db: Session = Depends(get_db)):
    """
    Return ALL practice sentences for a subject/textbook, grouped by lesson.

    Used by the top-bar 📖 diary overlay and the "My Sentences" diary
    section to show all sentences the student wrote in Step 5.

    Args:
        subject: e.g. "English"
        textbook: e.g. "Voca_8000" (empty string = all textbooks)
        db: Injected SQLAlchemy session.

    Returns:
        Dict with lessons (list of {lesson, sentences}) and total_sentences.
    """
    query = (
        db.query(UserPracticeSentence)
        .filter(UserPracticeSentence.subject == subject)
    )
    # Frontend may pass "all" (or empty) as a sentinel meaning "no textbook
    # filter" — needed because FastAPI path params can't match an empty
    # segment, so the URL would 404 if we required a real textbook.
    if textbook and textbook != "all":
        query = query.filter(UserPracticeSentence.textbook == textbook)

    rows = query.order_by(
        UserPracticeSentence.lesson,
        UserPracticeSentence.id.desc(),
    ).all()

    item_cache: dict[int, str] = {}
    lessons_map: dict[str, list] = {}
    for r in rows:
        if r.item_id not in item_cache:
            si = db.query(StudyItem.answer).filter(StudyItem.id == r.item_id).first()
            item_cache[r.item_id] = si.answer if si else ""
        word = item_cache[r.item_id]
        lessons_map.setdefault(r.lesson, []).append({
            "word": word,
            "sentence": r.sentence,
            "created_at": getattr(r, "created_at", "") or "",
        })

    lessons_list = [
        {"lesson": lesson, "sentences": sents}
        for lesson, sents in lessons_map.items()
    ]
    total = sum(len(l["sentences"]) for l in lessons_list)

    return {"lessons": lessons_list, "total_sentences": total}
