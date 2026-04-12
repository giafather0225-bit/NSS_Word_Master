"""pytest 공유 픽스처 — DB, FastAPI 테스트 클라이언트, 모의 응답."""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models import Lesson

# ── 인메모리 SQLite (테스트 전용) ─────────────────────────────────
# StaticPool: 모든 연결이 동일한 인메모리 DB를 공유 (세션 간 테이블 유지)
TEST_DB_URL = "sqlite://"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient — DB 세션을 인메모리 세션으로 교체."""
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_lesson(db_session) -> Lesson:
    """테스트용 Lesson 레코드."""
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


# ── Ollama / Gemini 모의 응답 ─────────────────────────────────────

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
