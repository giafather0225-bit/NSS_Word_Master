"""
services/ollama_manager.py — Ollama auto-start, health check, model pull
Section: System
Dependencies: httpx, subprocess
API: ensure_ollama(), ensure_ollama_once(), get_status(), shutdown_ollama()
"""

import os
import shutil
import subprocess
import threading
import time
from typing import Optional

import httpx

# ── Configuration ─────────────────────────────────────────────
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_EVAL_MODEL", "gemma2:2b")
PING_TIMEOUT = 1.5      # seconds per health probe
START_WAIT   = 8.0      # max seconds to wait for "ollama serve" to come up
PULL_TIMEOUT = 600.0    # 10 minutes for first-time model download

# Module-level state
_proc: Optional[subprocess.Popen] = None
_started_by_us: bool = False
_init_lock = threading.Lock()
_initialized: bool = False
_status: dict = {
    "running": False,
    "model_ready": False,
    "started_by_app": False,
    "last_error": None,
}


# @tag OLLAMA SYSTEM
def _ping() -> bool:
    """Return True if Ollama responds on /api/tags within PING_TIMEOUT."""
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=PING_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


# @tag OLLAMA SYSTEM
def _model_available() -> bool:
    """Check whether OLLAMA_MODEL is already pulled locally."""
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=PING_TIMEOUT)
        if r.status_code != 200:
            return False
        names = {m.get("name", "") for m in r.json().get("models", [])}
        # Match either exact tag or family prefix (e.g. "gemma2:2b" → "gemma2:2b")
        return any(n == OLLAMA_MODEL or n.startswith(OLLAMA_MODEL.split(":")[0]) for n in names)
    except Exception:
        return False


# @tag OLLAMA SYSTEM
def _pull_model() -> bool:
    """Trigger `ollama pull` for OLLAMA_MODEL. Blocks until complete or timeout."""
    try:
        r = httpx.post(
            f"{OLLAMA_HOST}/api/pull",
            json={"name": OLLAMA_MODEL, "stream": False},
            timeout=PULL_TIMEOUT,
        )
        return r.status_code == 200
    except Exception as e:
        _status["last_error"] = f"pull failed: {e}"
        return False


# @tag OLLAMA SYSTEM
def _spawn_ollama() -> bool:
    """Launch `ollama serve` as a background subprocess. Returns True on success."""
    global _proc, _started_by_us
    if shutil.which("ollama") is None:
        _status["last_error"] = "ollama binary not found in PATH"
        return False
    try:
        _proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        _started_by_us = True
        # Poll until /api/tags responds
        deadline = time.monotonic() + START_WAIT
        while time.monotonic() < deadline:
            if _ping():
                return True
            time.sleep(0.4)
        _status["last_error"] = "ollama serve did not respond within timeout"
        return False
    except Exception as e:
        _status["last_error"] = f"spawn failed: {e}"
        return False


# @tag OLLAMA SYSTEM STARTUP
def ensure_ollama() -> dict:
    """
    Ensure Ollama daemon is running and the eval model is pulled.

    1. Ping existing daemon → if up, skip spawn.
    2. Spawn `ollama serve` if missing.
    3. If the configured model isn't local, attempt `ollama pull`.

    Returns the current status dict (also stored at module level).
    """
    if _ping():
        _status["running"] = True
    else:
        _status["running"] = _spawn_ollama()

    if _status["running"]:
        if _model_available():
            _status["model_ready"] = True
        else:
            # Attempt async pull in the background — don't block startup
            try:
                _status["model_ready"] = _pull_model()
            except Exception as e:
                _status["last_error"] = f"pull error: {e}"

    _status["started_by_app"] = _started_by_us
    return dict(_status)


# @tag OLLAMA SYSTEM
def get_status() -> dict:
    """Return a fresh snapshot of Ollama status (re-pings the daemon)."""
    snap = dict(_status)
    snap["running"] = _ping()
    snap["model_ready"] = snap["running"] and _model_available()
    snap["started_by_app"] = _started_by_us
    return snap


# @tag OLLAMA SYSTEM SHUTDOWN
def shutdown_ollama() -> None:
    """Terminate the spawned Ollama subprocess if we started it."""
    global _proc, _started_by_us
    if _proc and _started_by_us:
        try:
            _proc.terminate()
            try:
                _proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                _proc.kill()
        except Exception:
            pass
    _proc = None
    _started_by_us = False
    _status["running"] = False
    _status["model_ready"] = False


# @tag OLLAMA SYSTEM
def ensure_ollama_once() -> None:
    """Lazy init: ensure Ollama is running. Thread-safe; no-op after first successful call."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        ensure_ollama()
        _initialized = True
