#!/usr/bin/env bash
# Vault Git Sync — Local Machine Side
# Pull latest Cloud Agent output from GitHub relay.
# Run manually or let the Local Approval Loop handle it with --auto-pull.

set -uo pipefail

VAULT_PATH="${VAULT_PATH:-./ai_employee_vault}"
BRANCH="${GIT_BRANCH:-main}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [vault-sync-local] $*"; }

cd "${VAULT_PATH}" || { echo "ERROR: Vault not found at ${VAULT_PATH}"; exit 1; }

log "Pulling latest vault changes from GitHub..."
git fetch origin "${BRANCH}" --quiet
git rebase "origin/${BRANCH}" --quiet && log "Up to date" || log "Rebase conflict — resolve manually"

# Show pending approvals summary
PENDING=$(find Pending_Approval/cloud -name "*.md" 2>/dev/null | wc -l)
log "Pending approvals: ${PENDING}"

if [[ ${PENDING} -gt 0 ]]; then
    echo ""
    echo "  Run approval review:"
    echo "  python -m src.orchestrator.local_approval_loop --vault ${VAULT_PATH}"
    echo ""
fi
