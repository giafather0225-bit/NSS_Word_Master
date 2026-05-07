#!/usr/bin/env bash
# ================================================================
# scripts/restore_from_backup.sh — Restore voca.db from a dated backup
# Section: System
# Dependencies: none (bash + sqlite3 optional for integrity check)
# Usage:
#   ./scripts/restore_from_backup.sh              # interactive: list + pick
#   ./scripts/restore_from_backup.sh voca_2026-05-06.db  # direct restore
#   ./scripts/restore_from_backup.sh --list       # list backups and exit
# ================================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────
DB_PATH="$HOME/NSS_Learning/database/voca.db"
BACKUP_DIR="$HOME/NSS_Learning/backups"
PREFIX="voca_"
SUFFIX=".db"

# ── Colors ───────────────────────────────────────────────────────
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLD='\033[1m'
RST='\033[0m'

# ── Helpers ──────────────────────────────────────────────────────
die()  { echo -e "${RED}ERROR: $*${RST}" >&2; exit 1; }
info() { echo -e "${BLD}$*${RST}"; }
ok()   { echo -e "${GRN}$*${RST}"; }
warn() { echo -e "${YLW}WARNING: $*${RST}"; }

human_size() {
  local bytes=$1
  if   (( bytes >= 1048576 )); then printf "%.1f MB" "$(echo "scale=1; $bytes/1048576" | bc)"
  elif (( bytes >= 1024 ));    then printf "%.1f KB" "$(echo "scale=1; $bytes/1024" | bc)"
  else printf "%d B" "$bytes"; fi
}

list_backups() {
  local files=()
  while IFS= read -r -d '' f; do
    files+=("$f")
  done < <(find "$BACKUP_DIR" -maxdepth 1 -name "${PREFIX}*${SUFFIX}" -print0 2>/dev/null | sort -rz)

  if [[ ${#files[@]} -eq 0 ]]; then
    warn "No backups found in $BACKUP_DIR"
    return 1
  fi

  echo ""
  printf "  %-5s  %-30s  %-10s  %s\n" "No." "Filename" "Size" "Modified"
  printf "  %-5s  %-30s  %-10s  %s\n" "----" "-----------------------------" "----------" "-------------------"
  local i=1
  for f in "${files[@]}"; do
    local name size mtime
    name=$(basename "$f")
    size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo "0")
    mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null \
         || stat -c "%y" "$f" 2>/dev/null | cut -c1-16 || echo "unknown")
    printf "  %-5s  %-30s  %-10s  %s\n" "[$i]" "$name" "$(human_size "$size")" "$mtime"
    (( i++ ))
  done
  echo ""
  echo "${files[@]}"
}

# ── Guard: backup dir must exist ─────────────────────────────────
[[ -d "$BACKUP_DIR" ]] || die "Backup directory not found: $BACKUP_DIR"

# ── --list mode ──────────────────────────────────────────────────
if [[ "${1:-}" == "--list" ]]; then
  info "Available backups:"
  list_backups > /dev/null || true
  exit 0
fi

# ── Collect backup files ─────────────────────────────────────────
mapfile -d '' BACKUP_FILES < <(
  find "$BACKUP_DIR" -maxdepth 1 -name "${PREFIX}*${SUFFIX}" -print0 2>/dev/null | sort -rz
)
[[ ${#BACKUP_FILES[@]} -gt 0 ]] || die "No backup files found in $BACKUP_DIR"

# ── Select backup ────────────────────────────────────────────────
SELECTED=""

if [[ -n "${1:-}" ]]; then
  # Direct argument: filename or path
  ARG="$1"
  [[ "$ARG" != /* ]] && ARG="$BACKUP_DIR/$ARG"
  [[ -f "$ARG" ]] || die "Backup file not found: $ARG"
  # Safety: must be inside BACKUP_DIR and match prefix
  REAL=$(realpath "$ARG")
  REAL_DIR=$(realpath "$BACKUP_DIR")
  [[ "$REAL" == "$REAL_DIR"/* ]] || die "Path traversal rejected: $ARG"
  [[ "$(basename "$REAL")" == ${PREFIX}* ]] || die "File does not look like a voca backup: $ARG"
  SELECTED="$REAL"
else
  # Interactive selection
  info "Available backups:"
  read -ra FILE_LIST <<< "$(list_backups)"
  # list_backups prints table to stdout + returns file list on last line
  # Re-run cleanly just for the array
  mapfile -d '' BACKUP_FILES < <(
    find "$BACKUP_DIR" -maxdepth 1 -name "${PREFIX}*${SUFFIX}" -print0 2>/dev/null | sort -rz
  )

  echo ""
  printf "  %-5s  %-30s  %-10s\n" "No." "Filename" "Size"
  printf "  %-5s  %-30s  %-10s\n" "----" "-----------------------------" "----------"
  local_i=1
  for f in "${BACKUP_FILES[@]}"; do
    local_size
    local_size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)
    printf "  %-5s  %-30s  %-10s\n" "[$local_i]" "$(basename "$f")" "$(human_size "$local_size")"
    (( local_i++ ))
  done
  echo ""

  read -rp "Select backup number (1-${#BACKUP_FILES[@]}), or q to quit: " CHOICE
  [[ "$CHOICE" == "q" ]] && { info "Aborted."; exit 0; }
  [[ "$CHOICE" =~ ^[0-9]+$ ]] || die "Invalid selection: $CHOICE"
  (( CHOICE >= 1 && CHOICE <= ${#BACKUP_FILES[@]} )) || die "Out of range: $CHOICE"
  SELECTED="${BACKUP_FILES[$((CHOICE-1))]}"
fi

SELECTED_NAME=$(basename "$SELECTED")
SELECTED_SIZE=$(stat -f%z "$SELECTED" 2>/dev/null || stat -c%s "$SELECTED" 2>/dev/null || echo 0)

# ── Confirm ───────────────────────────────────────────────────────
echo ""
warn "You are about to OVERWRITE the live database:"
echo "  Live DB  : $DB_PATH"
echo "  Restore  : $SELECTED_NAME  ($(human_size "$SELECTED_SIZE"))"
echo ""
echo "  The current DB will be saved as a safety copy before overwriting."
echo ""
read -rp "Type YES to confirm: " CONFIRM
[[ "$CONFIRM" == "YES" ]] || { info "Aborted."; exit 0; }

# ── Integrity check on backup ─────────────────────────────────────
if command -v sqlite3 &>/dev/null; then
  info "Running integrity check on backup..."
  INTEGRITY=$(sqlite3 "$SELECTED" "PRAGMA integrity_check;" 2>&1)
  if [[ "$INTEGRITY" != "ok" ]]; then
    warn "Integrity check failed: $INTEGRITY"
    read -rp "Continue anyway? (yes/no): " FORCE
    [[ "$FORCE" == "yes" ]] || { info "Aborted."; exit 1; }
  else
    ok "Integrity check passed."
  fi
fi

# ── Safety copy of current DB ─────────────────────────────────────
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SAFETY="$BACKUP_DIR/${PREFIX}pre-restore_${TIMESTAMP}${SUFFIX}"

if [[ -f "$DB_PATH" ]]; then
  info "Creating safety copy: $(basename "$SAFETY")"
  cp -p "$DB_PATH" "$SAFETY"
  ok "Safety copy saved: $SAFETY"
fi

# ── Stop server hint ─────────────────────────────────────────────
echo ""
warn "If the app server is running, it will reconnect to the restored DB automatically."
warn "For a clean restore it is recommended to stop the server first (Ctrl+C in the terminal running app.py)."
echo ""

# ── Restore ──────────────────────────────────────────────────────
info "Restoring $SELECTED_NAME → $DB_PATH ..."
cp -p "$SELECTED" "$DB_PATH"

# ── Verify restored DB ────────────────────────────────────────────
if command -v sqlite3 &>/dev/null; then
  CHECK=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>&1)
  if [[ "$CHECK" == "ok" ]]; then
    ok "Restored DB integrity check passed."
  else
    warn "Restored DB integrity check: $CHECK"
  fi
fi

# ── Done ─────────────────────────────────────────────────────────
echo ""
ok "================================================================"
ok " Restore complete."
ok "   From   : $SELECTED_NAME"
ok "   Safety : $(basename "$SAFETY")"
ok "   DB     : $DB_PATH"
ok "================================================================"
echo ""
info "To undo: run this script again and select the safety copy, or:"
echo "  cp \"$SAFETY\" \"$DB_PATH\""
