"""Shared pytest fixtures — DB, FastAPI test client, mock responses."""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models import Lesson

# ── In-memory SQLite (test only) ──────────────────────────────────
# StaticPool: all connections share the same in-memory DB (tables persist across sessions)
TEST_DB_URL = "sqlite://"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    # Tables managed outside ORM (raw SQL migrations) — create manually
    with eng.connect() as conn:
        conn.execute(
            __import__("sqlalchemy").text(
                "CREATE TABLE IF NOT EXISTS streak_freezes ("
                "  id           INTEGER PRIMARY KEY,"
                "  used_date    TEXT NOT NULL,"
                "  used_at      TEXT NOT NULL DEFAULT (datetime('now')),"
                "  inventory_id INTEGER"
                ")"
            )
        )
        conn.commit()
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def _reset_pin_rate_limiter(db_session):
    """Clear PIN rate-limit counters before each test.

    pin_guard.py persists failure counters as AppConfig rows
    (`pin_attempts_parent` / `pin_attempts_shop`) and commits them. Because the
    test engine is a single shared in-memory DB (StaticPool), those committed
    rows survive across tests — so tests that intentionally send wrong/no PIN
    accumulate the counter and later tests get HTTP 429. Wiping the rows up
    front restores per-test isolation.
    """
    from backend.models import AppConfig
    db_session.query(AppConfig).filter(
        AppConfig.key.like("pin_attempts_%")
    ).delete(synchronize_session=False)
    db_session.commit()
    yield


# Module attributes that bind a real-filesystem path at import time. Each is
# (dotted.module.ATTR, subpath-under-tmp-root or None for the root itself).
# Many modules do `from ..database import LEARNING_ROOT`, which copies the Path
# VALUE into their own namespace — so patching backend.database.LEARNING_ROOT
# alone does NOT redirect them. Every importer must be patched individually.
_REAL_FS_TARGETS = [
    ("backend.database.LEARNING_ROOT", None),
    ("backend.file_storage.LEARNING_ROOT", None),
    ("backend.file_storage.STORAGE_ROOT", "storage/lessons"),
    ("backend.main.VOCA_ROOT", "English/Voca_8000"),
    ("backend.routers.files.LEARNING_ROOT", None),
    ("backend.routers.lessons.LEARNING_ROOT", None),
    ("backend.routers.lessons.VOCA_ROOT", "English/Voca_8000"),
    ("backend.routers.diary_photo.LEARNING_ROOT", None),
    ("backend.routers.diary_photo._PHOTO_DIR", "diary_photos"),
    ("backend.routers.files_voca.LEARNING_ROOT", None),
    ("backend.routers.files_voca_ocr.LEARNING_ROOT", None),
    ("backend.routers.files_common.VOCA_ROOT", "English/Voca_8000"),
    ("backend.routers.words_mywords.LEARNING_ROOT", None),
    ("backend.routers.dashboard.LEARNING_ROOT", None),
    ("backend.routers.study.LEARNING_ROOT", None),
    ("backend.services.backup_engine.BACKUP_DIR", "backups"),
]


@pytest.fixture(autouse=True)
def _isolate_learning_root(tmp_path, monkeypatch):
    """Redirect every real-filesystem root to a per-test temp dir.

    Without this, upload/photo/backup/voca tests write into the user's real
    ~/NSS_Learning tree (lesson images, the child's actual diary photos, voca
    folders, DB backups). That both risks corrupting real data and leaks state
    across tests (observed: test_files persisting x.png into real storage;
    test_diary_photo / test_files_voca relying on fragile sentinel cleanup).

    Patching here — once, globally — guarantees no test can touch real user
    data and removes the need for each file to remember its own isolation.
    """
    root = tmp_path / "learning_root"
    for dotted, sub in _REAL_FS_TARGETS:
        value = root if sub is None else root / sub
        value.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(dotted, value, raising=False)
    yield


@pytest.fixture
def client(db_session):
    """FastAPI TestClient — replace the DB session with the in-memory session."""
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def ckla_seed(db_session):
    """Seed a minimal CKLA G3 domain + lesson + 3 questions.

    Returns a dict {domain, lesson, questions} for tests that need real
    referenced rows (e.g. lesson detail endpoint, question submission).
    """
    from datetime import datetime, timezone
    from backend.models import CKLADomain, CKLALesson, CKLAQuestion

    domain = CKLADomain(
        domain_num=1,
        title="Test Domain — Classic Tales",
        source_pdf="test.pdf",
        lesson_count=1,
        is_active=True,
        grade=3,
    )
    db_session.add(domain)
    db_session.flush()

    lesson = CKLALesson(
        domain_id=domain.id,
        domain_num=1,
        lesson_num=1,
        title="Test Lesson 1",
        passage="Once upon a time, there was a smoke test passage. " * 5,
        passage_chars=250,
        word_work_word="test",
        is_active=True,
        grade=3,
    )
    db_session.add(lesson)
    db_session.flush()

    questions = [
        CKLAQuestion(lesson_id=lesson.id, question_num=i + 1,
                     kind=kind, question_text=f"Test Q{i+1}",
                     model_answer="answer")
        for i, kind in enumerate(("literal", "literal", "inferential"))
    ]
    db_session.add_all(questions)
    db_session.commit()

    return {"domain": domain, "lesson": lesson, "questions": questions}


@pytest.fixture
def sample_lesson(db_session) -> Lesson:
    """A Lesson record for tests."""
    from datetime import datetime, timezone
    lesson = Lesson(
        subject="English",
        textbook="Voca_8000",
        lesson_name="Lesson_01",
        source_type="manual",
        description="",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)
    return lesson


# ── Ollama / Gemini mock responses ────────────────────────────────

MOCK_VOCAB_JSON = json.dumps([
    {
        "word": "abundant",
        "pos": "adj.",
        "definition": "existing in large quantities",
        "example": "The forest has abundant wildlife.",
    },
    {
        "word": "resilient",
        "pos": "adj.",
        "definition": "able to recover quickly from difficulties",
        "example": "She showed a resilient spirit after the setback.",
    },
])

MOCK_POOR_JSON = json.dumps([
    {"word": "abundant", "pos": "adj.", "definition": "abun", "example": ""},
])
