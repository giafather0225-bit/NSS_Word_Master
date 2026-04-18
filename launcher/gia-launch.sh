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
  git pull origin main 2>&1 | tee -a "$LOG_FILE"

  # Install deps if requirements.txt changed
  if git diff HEAD~1 --name-only 2>/dev/null | grep -q "requirements.txt"; then
    echo -e "${YELLOW}📚 Installing updated dependencies...${NC}"
    source "$VENV_DIR/bin/activate" 2>/dev/null
    pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
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
nohup uvicorn backend.main:app --host 0.0.0.0 --port $PORT \
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
