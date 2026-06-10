#!/usr/bin/env bash
# Vault Git Sync — Cloud Side
# Runs on Azure VM, pushes Cloud Agent output to GitHub relay every N seconds
# Local machine then does `git pull` to receive updates.
#
# Security: Only syncs markdown/state files.
# .gitignore must block: .env, *.json token files, whatsapp_session/, etc.

set -uo pipefail

VAULT_PATH="${VAULT_PATH:-/opt/ai_employee_vault}"
INTERVAL="${GIT_SYNC_INTERVAL:-60}"
BRANCH="${GIT_BRANCH:-main}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [vault-sync] $*"; }

log "Vault sync started — pushing to GitHub every ${INTERVAL}s"
log "Vault: ${VAULT_PATH} | Branch: ${BRANCH}"

while true; do
    cd "${VAULT_PATH}" 2>/dev/null || { log "ERROR: Vault path not found: ${VAULT_PATH}"; sleep 30; continue; }

    # Pull first to avoid conflicts
    git fetch origin "${BRANCH}" --quiet 2>/dev/null || true
    git rebase "origin/${BRANCH}" --quiet 2>/dev/null || true

    # Stage only markdown/state (secrets are .gitignored)
    git add "*.md" "Updates/" "Pending_Approval/" "In_Progress/" 2>/dev/null || true
    git add -A --ignore-errors 2>/dev/null || true

    # Only commit if there are changes
    if ! git diff --cached --quiet; then
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M UTC')
        git commit -m "cloud: vault sync ${TIMESTAMP}" --quiet
        git push origin "${BRANCH}" --quiet && log "Pushed changes to GitHub"
    fi

    sleep "${INTERVAL}"
done
