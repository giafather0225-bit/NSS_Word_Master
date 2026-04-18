"""
main.py — GIA Learning App entry point
Mounts static files, registers all API routers, and serves HTML page routes.
"""

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.append(str(Path(__file__).parent.parent))

from backend.database import Base, LEARNING_ROOT, engine
from backend.folder_watcher import start_watcher

from backend.routers import lessons, study, progress, words, files, tts, review, ai_coach
from backend.routers import xp as xp_router
from backend.routers import daily_words as daily_words_router
from backend.routers import reward_shop as reward_shop_router
from backend.routers import diary as diary_router
from backend.routers import diary_photo as diary_photo_router
from backend.routers import day_off as day_off_router
from backend.routers import diary_sentences as diary_sentences_router
from backend.routers import free_writing as free_writing_router
from backend.routers import calendar_api as calendar_router
from backend.routers import parent as parent_router
from backend.routers import parent_streak as parent_streak_router
from backend.routers import parent_xp as parent_xp_router
from backend.routers import growth_theme as growth_theme_router
from backend.routers import system as system_router
from backend.routers import reminder as reminder_router
from backend.routers import collocation as collocation_router
from backend.routers import math_academy as math_academy_router
from backend.routers import math_placement as math_placement_router
from backend.routers import math_fluency as math_fluency_router
from backend.routers import math_daily as math_daily_router
from backend.routers import math_kangaroo as math_kangaroo_router
from backend.routers import math_glossary as math_glossary_router
from backend.routers import math_problems as math_problems_router
from backend.routers import speech as speech_router
from backend.routers import arcade as arcade_router
from backend.routers import rewards as rewards_router
from backend.routers import schedules as schedules_router
from backend.routers import dashboard as dashboard_router
from backend.routers import tutor_sentence as tutor_sentence_router
from backend.services import ollama_manager, backup_engine

# ── DB init ────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Constants ──────────────────────────────────────────────
VOCA_ROOT = LEARNING_ROOT / "English" / "Voca_8000"

_executor = ThreadPoolExecutor(max_workers=2)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ── Lifespan ───────────────────────────────────────────────
_folder_observer = None

@asynccontextmanager
async def lifespan(application: FastAPI):
    global _folder_observer
    _folder_observer = start_watcher(VOCA_ROOT)

    # Phase 10: auto-backup DB (idempotent — no-op if today's snapshot exists)
    try:
        result = backup_engine.backup_database()
        if result.get("created"):
            logger.info("[backup] created %s", result.get("path"))
        if result.get("pruned"):
            logger.info("[backup] pruned %d old snapshot(s)", len(result["pruned"]))
    except Exception as e:
        logger.warning("[backup] startup backup failed: %s", e)

    # Phase 10: ensure Ollama daemon + eval model are ready (non-blocking on failure)
    try:
        status = ollama_manager.ensure_ollama()
        logger.info(
            "[ollama] running=%s model_ready=%s started_by_app=%s",
            status.get("running"), status.get("model_ready"), status.get("started_by_app"),
        )
    except Exception as e:
        logger.warning("[ollama] startup ensure failed: %s", e)

    yield

    if _folder_observer:
        _folder_observer.stop()
        _folder_observer.join()

    # Only kill Ollama if WE spawned it — don't disrupt a daemon the user was running
    try:
        ollama_manager.shutdown_ollama()
    except Exception:
        pass


# ── App setup ──────────────────────────────────────────────
app = FastAPI(title="NSS Word Master — Local Ollama + Mac TTS", lifespan=lifespan)

_CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

BASE_DIR      = Path(__file__).parent.parent
FRONTEND_DIR  = BASE_DIR / "frontend"
STATIC_DIR    = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

# ── PWA: serve SW and manifest from root scope ───────────
@app.get("/service-worker.js")
async def service_worker():
    """Serve service worker from root so it controls the full scope."""
    return FileResponse(STATIC_DIR / "service-worker.js", media_type="application/javascript")

@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest from root."""
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/json")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ── Routers ────────────────────────────────────────────────
app.include_router(lessons.router)
app.include_router(study.router)
app.include_router(progress.router)
app.include_router(words.router)
app.include_router(files.router)
app.include_router(tts.router)
app.include_router(review.router)
app.include_router(ai_coach.router)
app.include_router(xp_router.router)
app.include_router(daily_words_router.router)
app.include_router(reward_shop_router.router)
app.include_router(diary_router.router)
app.include_router(diary_photo_router.router)   # MUST come before diary_sentences (literal /photo wins over /{subject}/{textbook})
app.include_router(day_off_router.router)
app.include_router(diary_sentences_router.router)
app.include_router(free_writing_router.router)
app.include_router(calendar_router.router)
app.include_router(parent_router.router)
app.include_router(parent_streak_router.router)
app.include_router(parent_xp_router.router)
app.include_router(growth_theme_router.router)
app.include_router(system_router.router)
app.include_router(reminder_router.router)
app.include_router(collocation_router.router)
app.include_router(math_academy_router.router)
app.include_router(math_placement_router.router)
app.include_router(math_fluency_router.router)
app.include_router(math_daily_router.router)
app.include_router(math_kangaroo_router.router)
app.include_router(math_glossary_router.router)
app.include_router(math_problems_router.router)
app.include_router(speech_router.router)
app.include_router(arcade_router.router)
app.include_router(rewards_router.router)
app.include_router(schedules_router.router)
app.include_router(dashboard_router.router)
app.include_router(tutor_sentence_router.router)


# ── Static page routes ─────────────────────────────────────

# @tag PAGES
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon.svg or return 204 if missing."""
    from fastapi.responses import FileResponse
    path = Path(__file__).parent.parent / "frontend" / "static" / "favicon.svg"
    if path.exists():
        return FileResponse(str(path), media_type="image/svg+xml")
    return Response(status_code=204)


# @tag PAGES
@app.get("/")
def read_root(request: Request):
    """Serve the default child (GIA) UI."""
    return templates.TemplateResponse(name="child.html", request=request)


# @tag PAGES
@app.get("/child")
def read_child(request: Request):
    """Serve the child (GIA) UI."""
    return templates.TemplateResponse(name="child.html", request=request)


# @tag PAGES
@app.get("/ingest")
def read_ingest(request: Request):
    """Serve the parent ingest (OCR upload) UI."""
    return templates.TemplateResponse(name="parent_ingest.html", request=request)
