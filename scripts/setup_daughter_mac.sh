#!/usr/bin/env bash
# Initial setup on daughter's MacBook Air M1.
# Run once on the daughter's Mac:
#   bash setup_daughter_mac.sh
set -euo pipefail

REPO_URL="https://github.com/giafather0225-bit/NSS_Word_Master.git"
ROOT="$HOME/NSS_Learning"
APP_DIR="$ROOT/NSS_Word_Master"

echo "==> 1/6  Creating $ROOT"
mkdir -p "$ROOT"/{database,storage,backups,logs}

echo "==> 2/6  Checking Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "==> 3/6  Installing python@3.11 + git + tesseract"
brew list python@3.11 >/dev/null 2>&1 || brew install python@3.11
brew list git          >/dev/null 2>&1 || brew install git
brew list tesseract    >/dev/null 2>&1 || brew install tesseract

echo "==> 4/6  Cloning repo into $APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

echo "==> 5/6  Creating venv + installing requirements"
cd "$APP_DIR"
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> 6/6  Smoke test (starts server for 3 seconds)"
( python app.py & echo $! > /tmp/gia_pid ) >/dev/null 2>&1 || true
sleep 3
kill "$(cat /tmp/gia_pid)" 2>/dev/null || true

cat <<EOF

✅ Setup done.
   App dir : $APP_DIR
   Data    : $ROOT/{database,storage,backups,logs}

Start the server manually:
   cd $APP_DIR && source .venv/bin/activate && python app.py
Then open http://localhost:8000

Next step: ask dad to set up launchd auto-start (step 2).
EOF
