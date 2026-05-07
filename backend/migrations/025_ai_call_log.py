"""
migrations/025_ai_call_log.py — Create ai_call_log audit table
Section: System
Idempotent — safe to run multiple times (CREATE TABLE IF NOT EXISTS).

Purpose
-------
Records every Ollama / Gemini API call for:
  - PII audit (confirm no personal data is transmitted)
  - Performance monitoring (latency, quality scores)
  - Fallback tracking (how often Gemini is used)
  - Error diagnosis

Schema: see backend/models/assistant.py — AiCallLog
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"


# @tag SYSTEM BACKUP
def run_migration() -> None:
    """Create ai_call_log table. Idempotent."""
    if not DB_PATH.exists():
        print(f"[migration 025] DB not found at {DB_PATH} — skipped.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_call_log (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                provider         TEXT    NOT NULL,
                caller           TEXT    NOT NULL,
                prompt_summary   TEXT,
                response_summary TEXT,
                success          INTEGER NOT NULL DEFAULT 1,
                latency_ms       INTEGER,
                quality_score    REAL,
                fallback_used    INTEGER NOT NULL DEFAULT 0,
                error_message    TEXT,
                created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_ai_call_log_provider   ON ai_call_log(provider)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_ai_call_log_caller     ON ai_call_log(caller)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_ai_call_log_created_at ON ai_call_log(created_at)"
        )
        conn.commit()
        print("[migration 025] ai_call_log table ready.")
    except Exception as e:
        conn.rollback()
        print(f"[migration 025] ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
