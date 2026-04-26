#!/bin/bash
# ═══════════════════════════════════════════
# GIA Learning App — Server Stop
# ═══════════════════════════════════════════

APP_DIR="$HOME/Documents/GitHub/NSS_Word_Master"
PID_FILE="$APP_DIR/logs/server.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "✅ GIA server stopped (PID: $PID)"
  else
    rm -f "$PID_FILE"
    echo "⚠️ Server was not running."
  fi
else
  echo "⚠️ No PID file found."
  # Fallback: find and kill by port
  PID=$(lsof -ti:8000)
  if [ -n "$PID" ]; then
    kill $PID
    echo "✅ Killed process on port 8000 (PID: $PID)"
  fi
fi
