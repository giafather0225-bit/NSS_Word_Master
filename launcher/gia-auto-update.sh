#!/bin/bash
# ================================================================
#   gia-auto-update.sh — Auto-update GIA app from GitHub
#   Run via cron every 30 min on daughter's computer:
#     */30 * * * * $HOME/Documents/GitHub/NSS_Word_Master/launcher/gia-auto-update.sh >> $HOME/Documents/GitHub/NSS_Word_Master/logs/auto-update.log 2>&1
# ================================================================
# Design:
#   • Single venv (.venv) activated once at the top.
#   • Local edits are auto-stashed before pull (and popped at the end).
#   • Migrations are NEVER run here — main.py lifespan() applies them
#     exactly once via the `migrations_applied` tracker table.
#   • Bundle .min.js files are tracked in git (no node/npm required).
#   • Final health check verifies the server is actually serving.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$APP_DIR/.venv"
PID_FILE="$APP_DIR/logs/server.pid"
LOG_DIR="$APP_DIR/logs"
PORT=8000

cd "$APP_DIR" || { echo "[!] $APP_DIR not found"; exit 1; }
mkdir -p "$LOG_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*"; }

log "── Auto-update run ──"

# ─── Activate venv (one place only) ────────────────────────
if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  log "venv active: $(python3 --version 2>&1)"
else
  log "WARN: $VENV_DIR not found — using system python ($(python3 --version 2>&1))"
fi

# ─── Reset child.html (build.sh rewrites cache hash on every start) ───
git checkout -- frontend/templates/child.html 2>/dev/null || true

# ─── Stash any accidental local changes (so pull never fails) ──
STASHED=0
if ! git diff --quiet || ! git diff --cached --quiet; then
  log "Local changes detected — auto-stashing"
  if git stash push --include-untracked -m "auto-update-$(date +%s)" >/dev/null 2>&1; then
    STASHED=1
  else
    log "WARN: stash failed (continuing anyway)"
  fi
fi

# Always pop stash on exit, even if we bail early
cleanup() {
  if [ "$STASHED" = "1" ]; then
    if git stash pop >/dev/null 2>&1; then
      log "Local changes restored from stash"
    else
      log "WARN: could not pop stash — see 'git stash list'"
    fi
  fi
}
trap cleanup EXIT

# ─── Check GitHub for new commits ───
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null)

if ! git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 pull --ff-only origin main 2>&1; then
  log "git pull failed — leaving system unchanged"
  exit 0
fi

NEW_HEAD=$(git rev-parse HEAD 2>/dev/null)

if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
  log "Already up to date at $OLD_HEAD"
  exit 0
fi

log "Updated: ${OLD_HEAD:0:8} → ${NEW_HEAD:0:8}"
CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" 2>/dev/null)
log "Files changed: $(echo "$CHANGED" | wc -l | tr -d ' ')"

# ─── Install deps if requirements.txt changed ───
if echo "$CHANGED" | grep -q "^requirements.txt$"; then
  log "requirements.txt changed — running pip install"
  if ! pip install -q -r requirements.txt 2>&1 | tail -5; then
    log "WARN: pip install reported errors (continuing — server may still boot)"
  fi
fi

# ─── Migrations: server lifespan applies them (idempotent tracker) ───
if echo "$CHANGED" | grep -q "^backend/migrations/"; then
  log "New migrations detected — will apply on server restart:"
  echo "$CHANGED" | grep "^backend/migrations/" | sed "s|^|    |"
fi

# ─── Bundle changes — already shipped via git, log for visibility ───
if echo "$CHANGED" | grep -q "^frontend/static/js/bundle-"; then
  log "JS bundles updated"
fi

# ─── Stop old server ───
/usr/sbin/lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
sleep 2

# ─── Start new server ───
log "Starting new server on port $PORT"

# If running under LaunchAgent, let launchd restart it automatically
if launchctl list com.gia.learning >/dev/null 2>&1; then
  log "LaunchAgent detected — restarting via launchctl"
  launchctl stop com.gia.learning 2>/dev/null || true
  log "launchd will restart the server. Reload browser in ~15 seconds."
  exit 0
fi

# Fallback: no LaunchAgent — start directly
nohup python3 "$APP_DIR/app.py" >> "$LOG_DIR/server.log" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
log "Server PID: $NEW_PID"

# ─── Health check (up to 30s — lifespan runs migrations + build, can take a moment) ───
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null | grep -qE "200|301|302|307"; then
    log "✓ Server healthy at http://localhost:$PORT  (HEAD ${NEW_HEAD:0:8})"

    # Last 3 lifespan log lines for visibility (migration counts, etc.)
    if [ -f "$LOG_DIR/server.log" ]; then
      tail -20 "$LOG_DIR/server.log" | grep -E "\[migration\]|\[build\]|\[backup\]|\[island\]" | tail -5 | sed "s|^|    |"
    fi
    exit 0
  fi
  sleep 1
done

log "✗ ERROR: server did not respond within 30s"
log "  See $LOG_DIR/server.log for details. Last 20 lines:"
tail -20 "$LOG_DIR/server.log" 2>/dev/null | sed "s|^|    |"
exit 1
