#!/usr/bin/env bash
# ================================================================
#   update.sh — Pull latest code and restart the app
#   Run this on Gia's computer to get the newest version from Dad
# ================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== GIA Learning App — Update ==="
echo ""

# 1. Pull latest from GitHub
echo "[1/3] Downloading latest version..."
git pull origin main
echo ""

# 2. Install / sync Python packages
echo "[2/3] Updating packages..."
python3 -m pip install -q -r requirements.txt
echo "      Packages up to date."
echo ""

# 3. Copy .env if missing
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[!]   .env file created from template."
    echo "      Open .env and fill in your GEMINI_API_KEY if needed."
  fi
fi

echo "[3/3] Done."
echo ""
echo "Starting server at http://localhost:8000 ..."
echo "(Press Ctrl+C to stop)"
echo ""
python3 app.py
