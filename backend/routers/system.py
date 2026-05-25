"""
routers/system.py — System status, Ollama health, DB backup management,
                    self-update check on demand, asset diagnostic
Section: System
Dependencies: services/ollama_manager.py, services/backup_engine.py
API: GET /api/system/status, GET /api/system/ollama,
     POST /api/system/ollama/restart, GET /api/system/backups,
     POST /api/system/backups, POST /api/system/backups/restore,
     GET /api/system/check-update, POST /api/system/self-update,
     GET /api/system/asset-check
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from ..services import ollama_manager, backup_engine
    from ..routers.parent import require_parent_pin
except ImportError:
    from services import ollama_manager, backup_engine  # type: ignore
    from routers.parent import require_parent_pin  # type: ignore

router = APIRouter(prefix="/api/system", tags=["system"])
logger = logging.getLogger(__name__)

# Project root (two levels up from this file: backend/routers/system.py → repo)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Module-level cache for the upstream check — refreshed at most once per
# _UPDATE_CHECK_TTL seconds so frontend can poll cheaply.
_UPDATE_CHECK_TTL = 3600  # 1 hour
_update_cache: dict = {"checked_at": 0.0, "local_head": "", "remote_head": "", "update_available": False}


class RestoreRequest(BaseModel):
    filename: str = Field(max_length=200)


# @tag SYSTEM
@router.get("/status")
def system_status() -> dict:
    """Combined snapshot: Ollama status + backup count."""
    ollama = ollama_manager.get_status()
    backups = backup_engine.list_backups()
    return {
        "ollama": ollama,
        "backups": {
            "count": len(backups),
            "latest": backups[0] if backups else None,
        },
    }


# @tag OLLAMA SYSTEM
@router.get("/ollama")
def ollama_status() -> dict:
    """Return current Ollama daemon + model availability."""
    return ollama_manager.get_status()


# @tag OLLAMA SYSTEM
@router.post("/ollama/restart")
def ollama_restart(_pin: bool = Depends(require_parent_pin)) -> dict:
    """Stop the spawned Ollama process (if any) and re-run ensure_ollama()."""
    ollama_manager.shutdown_ollama()
    return ollama_manager.ensure_ollama()


# @tag BACKUP SYSTEM
@router.get("/backups")
def list_db_backups(_pin: bool = Depends(require_parent_pin)) -> dict:
    """List all DB backup files in ~/NSS_Learning/backups/."""
    return {"backups": backup_engine.list_backups()}


# @tag BACKUP SYSTEM
@router.post("/backups")
def trigger_backup(_pin: bool = Depends(require_parent_pin)) -> dict:
    """Force an immediate DB backup. No-op if today's backup already exists."""
    return backup_engine.backup_database()


# @tag BACKUP SYSTEM
@router.post("/backups/restore")
def restore_db_backup(
    req: RestoreRequest,
    _pin: bool = Depends(require_parent_pin),
) -> dict:
    """Restore a named backup. PIN-protected. Safety copy created first."""
    result = backup_engine.restore_backup(req.filename)
    if not result.get("restored"):
        raise HTTPException(status_code=400, detail=result.get("reason", "restore failed"))
    return result


# ─── Self-update (push-on-pull pattern for daughter Mac) ────────────────
# Daughter's app is launched on demand. On each app open, the frontend hits
# /api/system/check-update; if a newer commit exists upstream, the user is
# shown an "Updating…" page and POSTs /api/system/self-update, which spawns
# the gia-auto-update.sh script (detached) — that pulls + restarts the
# server. Cached for 1 hour so repeated page loads don't re-hit GitHub.

# @tag SYSTEM
@router.get("/check-update")
def check_update(force: bool = False) -> dict:
    """Cheap upstream-vs-local commit comparison, cached for 1h."""
    now = time.time()
    if not force and (now - _update_cache["checked_at"] < _UPDATE_CHECK_TTL):
        return {**_update_cache, "from_cache": True}

    try:
        local_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT), capture_output=True, timeout=3, text=True,
        )
        local_head = local_proc.stdout.strip() if local_proc.returncode == 0 else ""

        remote_proc = subprocess.run(
            ["git", "ls-remote", "origin", "main"],
            cwd=str(_REPO_ROOT), capture_output=True, timeout=5, text=True,
        )
        remote_head = ""
        if remote_proc.returncode == 0 and remote_proc.stdout:
            remote_head = remote_proc.stdout.split()[0]

        # Only fire when remote has commits we don't — not when we're ahead
        # of remote (dad's local commits awaiting push shouldn't trigger an
        # "Updating…" page on his machine).
        update_available = False
        if local_head and remote_head and local_head != remote_head:
            ancestor_proc = subprocess.run(
                ["git", "merge-base", "--is-ancestor", remote_head, "HEAD"],
                cwd=str(_REPO_ROOT), capture_output=True, timeout=3,
            )
            # exit 0 → remote_head is an ancestor of HEAD (local has it)
            # exit 1 → remote has a commit local doesn't (update available)
            # exit >1 → unknown commit (probably never fetched) → assume update
            update_available = ancestor_proc.returncode != 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("[update-check] failed: %s", exc)
        return {"update_available": False, "error": str(exc), "from_cache": False}
    _update_cache.update({
        "checked_at": now,
        "local_head": local_head[:8],
        "remote_head": remote_head[:8],
        "update_available": update_available,
    })
    return {**_update_cache, "from_cache": False}


def _check_kangaroo_pdf() -> dict:
    """Compare pdf_file values in Kangaroo JSON sets vs disk."""
    kangaroo_data_dir = _REPO_ROOT / "backend" / "data" / "math" / "kangaroo"
    pdf_dir = _REPO_ROOT / "frontend" / "static" / "math" / "kangaroo" / "pdf"

    expected: set[str] = set()
    if kangaroo_data_dir.is_dir():
        for jf in kangaroo_data_dir.glob("*.json"):
            try:
                d = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            pdf = d.get("pdf_file")
            if pdf:
                expected.add(Path(pdf).name)

    present: set[str] = {f.name for f in pdf_dir.glob("*.pdf")} if pdf_dir.is_dir() else set()
    missing = sorted(expected - present)
    return {
        "dir": str(pdf_dir),
        "expected": len(expected),
        "present": len(expected & present),
        "missing_count": len(missing),
        "missing": missing,
    }


def _check_island_png() -> dict:
    """Compare image paths in DB (characters + shop items) vs disk."""
    from ..database import SessionLocal  # local import — avoid module-load cost
    try:
        from ..models import IslandCharacter, IslandShopItem
    except ImportError:
        from models import IslandCharacter, IslandShopItem  # type: ignore

    island_root = _REPO_ROOT / "frontend" / "static" / "img" / "island"
    expected: set[str] = set()

    db = SessionLocal()
    try:
        # Characters: images JSON {stage_key: relative_path}
        for c in db.query(IslandCharacter).all():
            raw = c.images or ""
            if not raw:
                continue
            try:
                imgs = json.loads(raw)
            except Exception:
                continue
            for path in imgs.values():
                if path:
                    expected.add(str(path).lstrip("/"))

        # Shop items: image is a single relative path
        for it in db.query(IslandShopItem).all():
            if it.image:
                expected.add(str(it.image).lstrip("/"))
    finally:
        db.close()

    present: set[str] = set()
    missing: list[str] = []
    for rel in expected:
        if (island_root / rel).is_file():
            present.add(rel)
        else:
            missing.append(rel)

    missing.sort()
    return {
        "dir": str(island_root),
        "expected": len(expected),
        "present": len(present),
        "missing_count": len(missing),
        "missing": missing,
    }


# @tag SYSTEM
@router.get("/asset-check")
def asset_check() -> dict:
    """Report assets referenced by data/DB that are missing from disk.

    Two categories:
      • kangaroo_pdf — PDFs declared in JSON sets (intentionally git-untracked
        for copyright; copied manually per Mac)
      • island_png — PNG paths in island_characters.images + island_shop_items.image
        (git-tracked; if missing the daughter likely needs to re-pull or there
        is a service-worker cache problem)
    """
    return {
        "kangaroo_pdf": _check_kangaroo_pdf(),
        "island_png":   _check_island_png(),
    }


# @tag SYSTEM
@router.post("/self-update")
def self_update() -> dict:
    """Spawn gia-auto-update.sh detached. The script kills this server and
    starts a fresh one — current request still completes before the kill.

    Intentionally NOT PIN-gated: this is called from update-banner.js on the
    child's home screen during the auto-update flow. Origin is parent-owned
    git remote, so supply-chain risk is low; worst-case abuse from devtools
    is an unwanted restart, not code execution beyond what auto-update does
    anyway."""
    script = _REPO_ROOT / "launcher" / "gia-auto-update.sh"
    if not script.exists():
        raise HTTPException(status_code=404, detail="update script not found")

    log_dir = _REPO_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "auto-update.log"

    try:
        # Detach completely so killing the current uvicorn doesn't kill the
        # update script. start_new_session creates a new process group.
        log_fh = open(log_path, "ab")
        subprocess.Popen(
            ["bash", str(script)],
            cwd=str(_REPO_ROOT),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except Exception as exc:
        logger.exception("[self-update] spawn failed")
        raise HTTPException(status_code=500, detail=f"spawn failed: {exc}")

    # Invalidate cache so next /check-update reflects new HEAD
    _update_cache["checked_at"] = 0.0
    return {"spawned": True, "log_path": str(log_path)}
