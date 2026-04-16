"""
routers/system.py — System status, Ollama health, DB backup management
Section: System
Dependencies: services/ollama_manager.py, services/backup_engine.py
API: GET /api/system/status, GET /api/system/ollama,
     POST /api/system/ollama/restart, GET /api/system/backups,
     POST /api/system/backups, POST /api/system/backups/restore
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

try:
    from ..services import ollama_manager, backup_engine
    from ..routers.parent import require_parent_pin
except ImportError:
    from services import ollama_manager, backup_engine  # type: ignore
    from routers.parent import require_parent_pin  # type: ignore

router = APIRouter(prefix="/api/system", tags=["system"])


class RestoreRequest(BaseModel):
    filename: str


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
def ollama_restart() -> dict:
    """Stop the spawned Ollama process (if any) and re-run ensure_ollama()."""
    ollama_manager.shutdown_ollama()
    return ollama_manager.ensure_ollama()


# @tag BACKUP SYSTEM
@router.get("/backups")
def list_db_backups() -> dict:
    """List all DB backup files in ~/NSS_Learning/backups/."""
    return {"backups": backup_engine.list_backups()}


# @tag BACKUP SYSTEM
@router.post("/backups")
def trigger_backup() -> dict:
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
