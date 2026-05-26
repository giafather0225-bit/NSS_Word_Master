"""
main.py — GIA Learning App entry point
Mounts static files, registers all API routers, and serves HTML page routes.
"""

import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.append(str(Path(__file__).parent.parent))

from backend.database import Base, LEARNING_ROOT, SessionLocal, engine
from backend.folder_watcher import start_watcher

from backend.routers import lessons, study, progress, words, files, tts, review, ai_coach
from backend.routers import files_voca as files_voca_router
from backend.routers import files_voca_ocr as files_voca_ocr_router
from backend.routers import xp as xp_router
from backend.routers import daily_words as daily_words_router
from backend.routers import words_mywords as words_mywords_router
from backend.routers import reward_shop as reward_shop_router
from backend.routers import diary as diary_router
from backend.routers import diary_photo as diary_photo_router
from backend.routers import day_off as day_off_router
from backend.routers import diary_sentences as diary_sentences_router
from backend.routers import free_writing as free_writing_router
from backend.routers import calendar_api as calendar_router
from backend.routers import parent as parent_router
from backend.routers import parent_stats as parent_stats_router
from backend.routers import parent_math as parent_math_router
from backend.routers import parent_streak as parent_streak_router
from backend.routers import parent_xp as parent_xp_router
from backend.routers import parent_report as parent_report_router
from backend.routers import parent_ckla as parent_ckla_router
from backend.routers import starred as starred_router
from backend.routers import goals as goals_router
from backend.routers import system as system_router
from backend.routers import reminder as reminder_router
from backend.routers import collocation as collocation_router
from backend.routers import math_academy as math_academy_router
from backend.routers import math_academy_lifecycle as math_academy_lifecycle_router
from backend.routers import math_academy_flow as math_academy_flow_router
from backend.routers import math_spaced_review as math_spaced_review_router
from backend.routers import math_placement as math_placement_router
from backend.routers import math_fluency as math_fluency_router
from backend.routers import math_daily as math_daily_router
from backend.routers import math_kangaroo as math_kangaroo_router
from backend.routers import math_glossary as math_glossary_router
from backend.routers import math_problems as math_problems_router
from backend.routers import speech as speech_router
from backend.routers import arcade as arcade_router
from backend.routers import schedules as schedules_router
from backend.routers import dashboard as dashboard_router
from backend.routers import tutor_sentence as tutor_sentence_router
from backend.routers import ckla as ckla_router
from backend.routers import ckla_progress as ckla_progress_router
from backend.routers import ckla_domain_test as ckla_domain_test_router
from backend.routers import ckla_grade_test as ckla_grade_test_router
from backend.routers import island as island_router
from backend.routers import island_character as island_character_router
from backend.routers import island_shop as island_shop_router
from backend.routers import island_legend as island_legend_router
from backend.routers import island_dev as island_dev_router
from backend.routers import streak_freeze as streak_freeze_router
from backend.services import ollama_manager, backup_engine
from backend.services import island_care_engine as care
from backend.services import island_production_engine as prod

# ── DB init ────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Constants ──────────────────────────────────────────────
VOCA_ROOT = LEARNING_ROOT / "English" / "Voca_8000"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ── Lifespan ───────────────────────────────────────────────
_folder_observer = None

@asynccontextmanager
async def lifespan(application: FastAPI):
    global _folder_observer
    _folder_observer = start_watcher(VOCA_ROOT)

    # Auto-run all DB migrations on startup
    # Tracking table `migrations_applied` ensures each file runs exactly once.
    # On first boot after this change, all existing migrations re-run once (safe —
    # every migration is idempotent), then are recorded and skipped forever after.
    import importlib.util as _ilu
    import inspect as _inspect
    import sqlite3 as _sqlite3

    _DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"
    _mig_dir = Path(__file__).parent / "migrations"

    def _call_migration(_mod) -> bool:
        """Dispatch to whichever entry-point function the migration file defines.

        Handles all naming/signature conventions:
          migrate() / run_migration() / run() / main()  → no-arg
          run(conn: sqlite3.Connection)                  → open conn, pass it
          run(db_path: Path)                             → pass Path object
          run(db_path: str)                              → pass str(DB_PATH)
        Returns True if dispatched, False if no entry point found.
        """
        for _fname in ("migrate", "run_migration", "run", "main"):
            _fn = getattr(_mod, _fname, None)
            if _fn is None or not callable(_fn):
                continue
            _params = list(_inspect.signature(_fn).parameters.values())
            _required = [p for p in _params if p.default is _inspect.Parameter.empty]
            if not _params or not _required:
                _fn()
                return True
            _p = _required[0]
            _ann = _p.annotation
            _pname = _p.name.lower()
            if _ann is _sqlite3.Connection or "conn" in _pname:
                _c = _sqlite3.connect(str(_DB_PATH))
                try:
                    _fn(_c)
                    _c.commit()
                finally:
                    _c.close()
                return True
            if _ann is Path or "path" in _pname:
                _fn(_DB_PATH)
                return True
            _fn(str(_DB_PATH))
            return True
        return False

    # Bootstrap tracking table (runs before any migration)
    _track = _sqlite3.connect(str(_DB_PATH))
    _track.execute("""
        CREATE TABLE IF NOT EXISTS migrations_applied (
            filename   TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    _track.commit()

    _applied = _skipped = _failed = 0
    for _mig in sorted(_mig_dir.glob("[0-9]*.py")):
        # Skip if already recorded
        if _track.execute(
            "SELECT 1 FROM migrations_applied WHERE filename = ?", (_mig.name,)
        ).fetchone():
            _skipped += 1
            continue
        try:
            _spec = _ilu.spec_from_file_location(_mig.stem, _mig)
            _mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            if not _call_migration(_mod):
                logger.debug("[migration] %s — no entry point, skipped", _mig.name)
                continue
            _track.execute(
                "INSERT OR IGNORE INTO migrations_applied (filename) VALUES (?)",
                (_mig.name,),
            )
            _track.commit()
            _applied += 1
            logger.info("[migration] applied %s", _mig.name)
        except (Exception, SystemExit) as _e:
            _failed += 1
            logger.warning("[migration] %s failed: %s", _mig.name, _e)

    _track.close()
    logger.info(
        "[migration] done — applied=%d  skipped=%d  failed=%d",
        _applied, _skipped, _failed,
    )

    # ── PIN strength check ────────────────────────────────────
    # Parent functions (XP rules, day-off approval, weekly report, system
    # backup, Reward Shop "use") are gated only by a 4-digit PIN. If the
    # parent never set one, the fallback DEFAULT_PIN ("0000") guards every-
    # thing — trivial for a 9yo to bypass. Log a loud warning so the parent
    # notices, and refuse to boot if STRICT_PIN=1 is set.
    try:
        from backend.services import pin_hash as _pin_hash
        _pcheck = _sqlite3.connect(str(_DB_PATH))
        _row = _pcheck.execute(
            "SELECT value FROM app_config WHERE key = 'pin'"
        ).fetchone()
        _pcheck.close()
        _stored = _row[0] if _row else ""
        _weak = False
        _reason = ""
        if not _stored:
            _weak = True
            _reason = "no PIN set — DEFAULT_PIN fallback in use"
        elif not _pin_hash.is_hashed(_stored) and _pin_hash.is_weak_pin(_stored):
            _weak = True
            _reason = "stored PIN is a trivially-guessable plaintext value"
        if _weak:
            _msg = (
                "\n" + "!" * 72 +
                f"\n[security] Parent PIN is weak: {_reason}.\n"
                "[security] A child can bypass parent controls (day-off approval,\n"
                "[security] XP rules, system backup, Reward Shop). Set a non-trivial\n"
                "[security] PIN via Parent Dashboard → Settings → Account.\n" +
                "!" * 72
            )
            if os.getenv("STRICT_PIN") == "1":
                logger.error(_msg)
                raise SystemExit(
                    "STRICT_PIN=1 and parent PIN is weak — refusing to boot."
                )
            logger.warning(_msg)
    except SystemExit:
        raise
    except Exception as _e:
        logger.warning("[security] PIN strength check skipped: %s", _e)

    # Phase 10: auto-backup DB (idempotent — no-op if today's snapshot exists)
    try:
        result = backup_engine.backup_database()
        if result.get("created"):
            logger.info("[backup] created %s", result.get("path"))
        if result.get("pruned"):
            logger.info("[backup] pruned %d old snapshot(s)", len(result["pruned"]))
    except Exception as e:
        logger.warning("[backup] startup backup failed: %s", e)

    # Ollama starts lazily on first AI request (see ollama_manager.ensure_ollama_once)

    # Auto-rebuild JS bundles so JS edits take effect on server restart
    _build_sh = Path(__file__).parent.parent / "build.sh"
    if _build_sh.exists():
        try:
            r = subprocess.run(["bash", str(_build_sh)], capture_output=True, timeout=30, cwd=str(_build_sh.parent))
            if r.returncode == 0:
                logger.info("[build] JS bundles rebuilt")
            else:
                logger.warning("[build] bundle rebuild failed (using existing): %s", r.stderr.decode()[:200])
        except Exception as e:
            logger.warning("[build] bundle rebuild skipped: %s", e)

    # Island: daily gauge decay + completed-character Lumi production
    try:
        db = SessionLocal()
        try:
            decay_result = care.run_daily_batch(db)
            prod_result = prod.run_daily_production(db)
            db.commit()
            broken = decay_result.get("legend_streak_broken", [])
            logger.info(
                "[island] decay processed=%d skipped=%d legend_breaks=%d | lumi produced=%d characters=%d",
                decay_result["processed"], decay_result["skipped"], len(broken),
                prod_result["produced"], prod_result["characters"],
            )
        except Exception as e:
            db.rollback()
            logger.warning("[island] startup batch failed: %s", e)
        finally:
            db.close()
    except Exception as e:
        logger.warning("[island] startup batch DB error: %s", e)

    yield

    if _folder_observer:
        _folder_observer.stop()
        _folder_observer.join()

    # Only kill Ollama if WE spawned it — don't disrupt a daemon the user was running
    try:
        ollama_manager.shutdown_ollama()
    except Exception as exc:
        logger.warning("Ollama shutdown failed (non-fatal): %s", exc)


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

_ALLOWED_ORIGINS: frozenset[str] = frozenset(_CORS_ORIGINS)
_MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@app.middleware("http")
async def csrf_origin_guard(request: Request, call_next):
    """Reject state-changing requests whose Origin header is set but not in the allow-list.

    Browsers always send Origin on cross-site requests; same-site requests and
    direct curl/app calls omit it — those are allowed through.
    """
    if request.method in _MUTATING_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and origin not in _ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Cross-origin state-change rejected."},
            )
    return await call_next(request)


# ── Validation error → child-friendly 422 JSON ───────────────
# Replaces the old silent ``.strip()[:N]`` pattern. When a payload field is
# too long (or missing), the frontend receives a clear message it can toast,
# instead of data being silently truncated before saving.
_FIELD_LABELS = {
    "title": "Title", "content": "Text", "reason": "Reason", "memo": "Memo",
    "word": "Word", "definition": "Definition", "example": "Example",
    "sentence": "Sentence", "description": "Description",
    "textbook": "Textbook", "lesson": "Lesson", "stage": "Stage",
    "collocation": "Phrase", "user_answer": "Your answer",
    "request_date": "Date", "test_date": "Date", "entry_date": "Date",
}


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """Turn Pydantic errors into one short user-facing message + structured field list."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = [str(p) for p in first.get("loc", []) if p not in ("body",)]
    field_key = loc[-1] if loc else ""
    label = _FIELD_LABELS.get(field_key, field_key.replace("_", " ").title() or "Input")
    err_type = first.get("type", "")
    ctx = first.get("ctx", {}) or {}

    if "string_too_long" in err_type or "too_long" in err_type:
        limit = ctx.get("max_length", "")
        message = f"{label} is too long — please shorten it (max {limit} characters)."
    elif "missing" in err_type:
        message = f"{label} is required."
    elif "string_type" in err_type or "type_error" in err_type:
        message = f"{label} has an invalid format."
    else:
        message = f"{label}: {first.get('msg', 'invalid value')}"

    return JSONResponse(
        status_code=422,
        content={"message": message, "field": field_key, "errors": errors},
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
app.include_router(words_mywords_router.router)
app.include_router(files.router)
app.include_router(files_voca_router.router)
app.include_router(files_voca_ocr_router.router)
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
app.include_router(parent_stats_router.router)
app.include_router(parent_math_router.router)
app.include_router(parent_streak_router.router)
app.include_router(streak_freeze_router.router)
app.include_router(parent_xp_router.router)
app.include_router(parent_report_router.router)
app.include_router(starred_router.router)
app.include_router(goals_router.router)
app.include_router(system_router.router)
app.include_router(reminder_router.router)
app.include_router(collocation_router.router)
app.include_router(math_academy_router.router)
app.include_router(math_academy_lifecycle_router.router)
app.include_router(math_academy_flow_router.router)
app.include_router(math_spaced_review_router.router)
app.include_router(math_placement_router.router)
app.include_router(math_fluency_router.router)
app.include_router(math_daily_router.router)
app.include_router(math_kangaroo_router.router)
app.include_router(math_glossary_router.router)
app.include_router(math_problems_router.router)
app.include_router(speech_router.router)
app.include_router(arcade_router.router)
app.include_router(schedules_router.router)
app.include_router(dashboard_router.router)
app.include_router(tutor_sentence_router.router)
app.include_router(ckla_router.router)
app.include_router(ckla_progress_router.router)
app.include_router(ckla_domain_test_router.router)
app.include_router(ckla_grade_test_router.router)
app.include_router(parent_ckla_router.router)
app.include_router(island_router.router)
app.include_router(island_character_router.router)
app.include_router(island_shop_router.router)
app.include_router(island_legend_router.router)
app.include_router(island_dev_router.router)


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
    """Serve the default child (GIA) UI. Update banner injected client-side
    via static/js/update-banner.js — no forced redirect."""
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


# @tag PAGES SYSTEM
@app.get("/asset-check")
def read_asset_check(request: Request):
    """Diagnostic page: which expected files are missing from disk?"""
    return templates.TemplateResponse(name="asset_check.html", request=request)
