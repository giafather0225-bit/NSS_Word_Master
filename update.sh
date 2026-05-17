#!/usr/bin/env bash
# ================================================================
#   update.sh — Manual pull + restart (run on daughter's Mac)
#
#   What this does:
#     1. Auto-stash any local edits (popped at the end)
#     2. git pull --ff-only
#     3. pip install IF requirements.txt changed
#     4. Start the server (lifespan handles migrations + bundle build)
#     5. Print HEAD + key startup log lines so you can see what changed
# ================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== GIA Learning App — Update ==="
echo ""

# ─── 1. Activate venv if present ────────────────────────────
if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  echo "[venv] $(python3 --version 2>&1)"
else
  echo "[!]  .venv not found — using system python ($(python3 --version 2>&1))"
  echo "    For best results, run scripts/setup_daughter_mac.sh first."
fi
echo ""

# ─── 2. Auto-stash local changes so pull never fails ───────
STASHED=0
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "[1/4] Local changes detected — auto-stashing"
  if git stash push --include-untracked -m "manual-update-$(date +%s)" >/dev/null 2>&1; then
    STASHED=1
  fi
else
  echo "[1/4] Working tree clean"
fi
echo ""

cleanup() {
  if [ "$STASHED" = "1" ]; then
    if git stash pop >/dev/null 2>&1; then
      echo "[*]  Restored your local changes"
    else
      echo "[!]  Could not auto-restore — run 'git stash pop' manually"
    fi
  fi
}
trap cleanup EXIT

# ─── 3. Pull ─────────────────────────────────────────────────
echo "[2/4] Downloading latest version..."
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null)
if ! git pull --ff-only origin main; then
  echo "[!]  git pull failed — please resolve before retrying"
  exit 1
fi
NEW_HEAD=$(git rev-parse HEAD 2>/dev/null)
if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
  echo "      Already up to date at ${OLD_HEAD:0:8}"
else
  echo "      ${OLD_HEAD:0:8} → ${NEW_HEAD:0:8}"
fi
echo ""

# ─── 4. pip install only when requirements changed ─────────
CHANGED=$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" 2>/dev/null)
if echo "$CHANGED" | grep -q "^requirements.txt$"; then
  echo "[3/4] requirements.txt changed — running pip install..."
  python3 -m pip install -q --upgrade pip
  python3 -m pip install -q -r requirements.txt
  echo "      Packages up to date."
else
  echo "[3/4] No dep changes — skipping pip install"
fi
echo ""

# ─── 5. .env safety ─────────────────────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[*]   .env file created from template — fill in GEMINI_API_KEY if needed."
fi

# ─── 6. Start server (lifespan handles migrations + bundle rebuild) ─
echo "[4/4] Starting server at http://localhost:8000 ..."
echo "      (Press Ctrl+C to stop)"
echo ""
exec python3 app.py
