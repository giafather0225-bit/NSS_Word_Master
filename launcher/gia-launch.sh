#!/bin/bash
# ═══════════════════════════════════════════
# GIA Learning App Launcher
# MacBook Air M1
# ═══════════════════════════════════════════

# ─── Config ───
APP_DIR="$HOME/NSS_Learning/NSS_Word_Master"
VENV_DIR="$APP_DIR/.venv"
PORT=8000
LOG_FILE="$APP_DIR/logs/server.log"
PID_FILE="$APP_DIR/logs/server.pid"
AUTO_UPDATE=true    # Auto git pull on launch

# ─── Colors ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Log directory ───
mkdir -p "$APP_DIR/logs"

echo -e "${GREEN}🌟 Starting GIA Learning App...${NC}"

# ─── Move to project directory ───
cd "$APP_DIR" || {
  echo -e "${RED}❌ Project directory not found: $APP_DIR${NC}"
  osascript -e 'display alert "GIA Error" message "Project directory not found. Please check the path."'
  exit 1
}

# ─── Auto-update (only when flag is true) ───
if [ "$AUTO_UPDATE" = true ]; then
  echo -e "${YELLOW}📦 Checking for updates...${NC}"
  OLD_HEAD=$(git rev-parse HEAD 2>/dev/null)
  # Abort git pull on slow/flaky wifi (hotels, planes) to avoid blocking startup
  export GIT_HTTP_LOW_SPEED_LIMIT=1000
  export GIT_HTTP_LOW_SPEED_TIME=10
  if ! git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 pull origin main 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${RED}⚠️ git pull failed — continuing with current code.${NC}"
    osascript -e 'display notification "Update failed — using current version." with title "GIA"' 2>/dev/null
  else
    NEW_HEAD=$(git rev-parse HEAD 2>/dev/null)
    CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" 2>/dev/null)

    # Install deps if requirements.txt changed
    if echo "$CHANGED" | grep -q "requirements.txt"; then
      echo -e "${YELLOW}📚 Installing updated dependencies...${NC}"
      source "$VENV_DIR/bin/activate" 2>/dev/null
      pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
    fi

    # Run new migrations if any
    if echo "$CHANGED" | grep -q "backend/migrations/"; then
      echo -e "${YELLOW}🗄️  Applying database migrations...${NC}"
      source "$VENV_DIR/bin/activate" 2>/dev/null
      for mig in backend/migrations/[0-9]*.py; do
        [ -f "$mig" ] || continue
        echo "  → $(basename "$mig")" | tee -a "$LOG_FILE"
        python3 "$mig" 2>&1 | tee -a "$LOG_FILE"
      done
    fi
  fi
fi

# ─── Check if already running ───
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo -e "${GREEN}✅ Server already running (PID: $OLD_PID)${NC}"
    echo -e "${GREEN}🌐 Opening GIA...${NC}"
    open -na "Google Chrome" --args --app="http://localhost:$PORT/child"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

# ─── Activate venv ───
if [ -d "$VENV_DIR" ]; then
  source "$VENV_DIR/bin/activate"
else
  echo -e "${YELLOW}⚠️ No venv found. Using system Python.${NC}"
fi

# ─── Start server (background) ───
echo -e "${GREEN}🚀 Starting server on port $PORT...${NC}"
nohup uvicorn backend.main:app --host 127.0.0.1 --port $PORT \
  >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# ─── Wait for server ready (max 15s) ───
echo -e "${YELLOW}⏳ Waiting for server...${NC}"
for i in $(seq 1 30); do
  if curl -s "http://localhost:$PORT/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server ready!${NC}"
    break
  fi
  sleep 0.5
done

# ─── Verify server ───
if ! curl -s "http://localhost:$PORT/" > /dev/null 2>&1; then
  echo -e "${RED}❌ Server failed to start. Check logs: $LOG_FILE${NC}"
  osascript -e 'display alert "GIA Error" message "Server failed to start. Check the logs."'
  exit 1
fi

# ─── Open Chrome in PWA mode ───
echo -e "${GREEN}🌐 Opening GIA...${NC}"
open -na "Google Chrome" --args --app="http://localhost:$PORT/child"

echo -e "${GREEN}🎉 GIA is ready! Have fun learning!${NC}"
echo -e "${YELLOW}💡 To stop: $APP_DIR/launcher/gia-stop.sh${NC}"
