"""
services/backup_engine.py — SQLite DB auto-backup with rolling retention
Section: System
Dependencies: shutil, pathlib (stdlib only)
API: backup_database(), list_backups(), restore_backup(filename)
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

try:
    from ..database import DB_PATH, LEARNING_ROOT
except ImportError:
    from database import DB_PATH, LEARNING_ROOT  # type: ignore

# ── Configuration ─────────────────────────────────────────────
BACKUP_DIR = LEARNING_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
RETENTION_DAYS = 7  # keep last 7 daily backups
PREFIX = "voca_"
SUFFIX = ".db"


# @tag BACKUP SYSTEM STARTUP
def backup_database() -> dict:
    """
    Copy ~/NSS_Learning/database/voca.db → ~/NSS_Learning/backups/voca_YYYY-MM-DD.db.

    Uses sqlite3 .backup() API for a consistent snapshot even while the DB is
    open in WAL mode. If today's backup already exists, this is a no-op.

    Returns: {"created": bool, "path": str|None, "pruned": [filenames]}
    """
    if not Path(DB_PATH).exists():
        return {"created": False, "path": None, "pruned": [], "reason": "source db missing"}

    today = datetime.now().strftime("%Y-%m-%d")
    target = BACKUP_DIR / f"{PREFIX}{today}{SUFFIX}"

    created = False
    if not target.exists():
        try:
            src = sqlite3.connect(str(DB_PATH))
            dst = sqlite3.connect(str(target))
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
            created = True
        except Exception:
            # Fall back to a raw file copy — slightly less safe but better than nothing
            try:
                shutil.copy2(DB_PATH, target)
                created = True
            except Exception as e:
                return {"created": False, "path": None, "pruned": [], "reason": str(e)}

    pruned = _prune_old_backups()
    return {"created": created, "path": str(target), "pruned": pruned}


# @tag BACKUP SYSTEM
def _prune_old_backups() -> List[str]:
    """Delete backups older than the most recent RETENTION_DAYS files."""
    backups = sorted(
        BACKUP_DIR.glob(f"{PREFIX}*{SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    pruned: List[str] = []
    for old in backups[RETENTION_DAYS:]:
        try:
            old.unlink()
            pruned.append(old.name)
        except Exception:
            continue
    return pruned


# @tag BACKUP SYSTEM
def list_backups() -> List[dict]:
    """Return metadata for all current backup files (newest first)."""
    out: List[dict] = []
    for p in sorted(
        BACKUP_DIR.glob(f"{PREFIX}*{SUFFIX}"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    ):
        try:
            stat = p.stat()
            out.append({
                "filename": p.name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            })
        except Exception:
            continue
    return out


# @tag BACKUP SYSTEM
def restore_backup(filename: str) -> dict:
    """
    Restore a backup file over the live DB. The current DB is first copied to
    voca_pre-restore_<timestamp>.db so the operation is reversible.

    Returns: {"restored": bool, "from": filename, "safety_copy": str|None}
    """
    src = (BACKUP_DIR / filename).resolve()
    if not str(src).startswith(str(BACKUP_DIR.resolve())) or not src.exists() \
            or not src.name.startswith(PREFIX):
        return {"restored": False, "from": filename, "safety_copy": None,
                "reason": "backup not found or invalid path"}

    safety_copy = None
    try:
        if Path(DB_PATH).exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety = BACKUP_DIR / f"{PREFIX}pre-restore_{ts}{SUFFIX}"
            shutil.copy2(DB_PATH, safety)
            safety_copy = str(safety)
        shutil.copy2(src, DB_PATH)
        return {"restored": True, "from": filename, "safety_copy": safety_copy}
    except Exception as e:
        return {"restored": False, "from": filename, "safety_copy": safety_copy,
                "reason": str(e)}
