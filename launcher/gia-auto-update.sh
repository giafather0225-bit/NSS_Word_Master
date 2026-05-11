#!/bin/bash
# ================================================================
#   gia-auto-update.sh — Auto-update GIA app from GitHub
#   Run via cron every 30 min on daughter's computer:
#     */30 * * * * $HOME/Documents/GitHub/NSS_Word_Master/launcher/gia-auto-update.sh >> $HOME/Documents/GitHub/NSS_Word_Master/logs/auto-update.log 2>&1
# ================================================================

APP_DIR="$HOME/Documents/GitHub/NSS_Word_Master"
VENV_DIR="$APP_DIR/.venv"
PID_FILE="$APP_DIR/logs/server.pid"
PORT=8000

cd "$APP_DIR" || exit 1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking for updates..."

# ─── Check GitHub for new commits ───
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null)

export GIT_HTTP_LOW_SPEED_LIMIT=1000
export GIT_HTTP_LOW_SPEED_TIME=10
if ! git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 pull origin main 2>&1; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] git pull failed — skipping."
  exit 0
fi

NEW_HEAD=$(git rev-parse HEAD 2>/dev/null)

# ─── No changes — nothing to do ───
if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Already up to date."
  exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] New version detected: $OLD_HEAD -> $NEW_HEAD"
CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" 2>/dev/null)

# ─── Install deps if requirements.txt changed ───
if echo "$CHANGED" | grep -q "requirements.txt"; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installing updated dependencies..."
  source "$VENV_DIR/bin/activate" 2>/dev/null
  pip install -r requirements.txt
fi

# ─── Run new migrations ───
if echo "$CHANGED" | grep -q "backend/migrations/"; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running migrations..."
  source "$VENV_DIR/bin/activate" 2>/dev/null
  for mig in backend/migrations/[0-9]*.py; do
    [ -f "$mig" ] || continue
    echo "[$(date '+%Y-%m-%d %H:%M:%S')]   -> $(basename "$mig")"
    python3 "$mig"
  done
fi

# ─── Restart server ───
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping old server (PID: $OLD_PID)..."
    kill "$OLD_PID"
    sleep 2
  fi
  rm -f "$PID_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting new server..."
source "$VENV_DIR/bin/activate" 2>/dev/null
nohup uvicorn backend.main:app --host 127.0.0.1 --port $PORT \
  >> "$APP_DIR/logs/server.log" 2>&1 &
echo $! > "$PID_FILE"

# ─── Wait and verify ───
for i in $(seq 1 20); do
  if curl -s "http://localhost:$PORT/" > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Server restarted successfully."
    exit 0
  fi
  sleep 1
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Server failed to restart. Check server.log."
exit 1
