#!/bin/bash
APP_DIR="$HOME/NSS_Learning/NSS_Word_Master"
LOG_DIR="$HOME/NSS_Learning/logs"
mkdir -p "$LOG_DIR"
cd "$APP_DIR" || exit 1
/usr/sbin/lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1
git checkout -- frontend/templates/child.html 2>/dev/null || true
GIT_HTTP_LOW_SPEED_LIMIT=1000 GIT_HTTP_LOW_SPEED_TIME=10 \
  git pull origin main 2>>"$LOG_DIR/gia-stderr.log" || true
python3 -m pip install -q -r requirements.txt 2>>"$LOG_DIR/gia-stderr.log" || true
find "$APP_DIR/backend" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
exec python3 "$APP_DIR/app.py"
