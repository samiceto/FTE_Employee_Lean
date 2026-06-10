#!/usr/bin/env bash
# Vault GitHub Relay Setup
# Run this ONCE on your local machine to create the GitHub-synced vault repo
#
# After this script:
#   - Your vault is a git repo pushed to GitHub
#   - Cloud VM can clone it and push updates
#   - Local machine pulls updates and reviews approvals
#
# Prerequisites:
#   - GitHub CLI installed: https://cli.github.com/
#   - gh auth login completed
#   - Or: create repo manually and set VAULT_GITHUB_REPO below

set -euo pipefail

VAULT_PATH="${VAULT_PATH:-./ai_employee_vault}"
REPO_NAME="${REPO_NAME:-ai-employee-vault}"
GITHUB_USER="${GITHUB_USER:-$(gh api user --jq .login 2>/dev/null || echo '')}"
VISIBILITY="${VISIBILITY:-private}"

log()  { echo "[vault-setup] $*"; }
err()  { echo "[ERROR] $*"; exit 1; }

cd "${VAULT_PATH}" || err "Vault not found: ${VAULT_PATH}"

# ── Initialize git repo if needed ─────────────────────────────────────
if [[ ! -d .git ]]; then
    log "Initializing git repo in vault..."
    git init
    git branch -M main
fi

# ── Create .gitignore if not present ──────────────────────────────────
if [[ ! -f .gitignore ]]; then
    log "Creating vault .gitignore..."
    cat > .gitignore << 'EOF'
.env
.env.*
*.token
token.json
*_token.json
credentials.json
*_credentials.json
client_secret*.json
whatsapp_session/
*_user_data/
*.db
*.sqlite
EOF
fi

# ── Initial commit ────────────────────────────────────────────────────
git add -A
if ! git diff --cached --quiet; then
    git commit -m "Initial vault commit — Platinum Tier setup"
fi

# ── Create GitHub repo ────────────────────────────────────────────────
if command -v gh &>/dev/null && [[ -n "${GITHUB_USER}" ]]; then
    log "Creating GitHub repo: ${GITHUB_USER}/${REPO_NAME} (${VISIBILITY})..."
    gh repo create "${REPO_NAME}" \
        --${VISIBILITY} \
        --description "AI Employee Vault — state sync between Cloud and Local agents" \
        --source . \
        --remote origin \
        --push || log "Repo may already exist — trying push..."
    git push -u origin main 2>/dev/null || true
    REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
else
    log "GitHub CLI not available — set remote manually:"
    log "  git remote add origin https://github.com/YOUR_USER/${REPO_NAME}.git"
    log "  git push -u origin main"
    REPO_URL="https://github.com/YOUR_USER/${REPO_NAME}.git"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Vault GitHub Relay Ready!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Vault repo: ${REPO_URL}"
echo ""
echo "  On Azure VM, set in azure_vm_setup.sh:"
echo "    VAULT_REPO_URL=${REPO_URL}"
echo ""
echo "  The Cloud Agent will:"
echo "    - Clone this repo on the VM"
echo "    - Push drafts every 60s"
echo ""
echo "  On local machine, receive updates:"
echo "    bash scripts/cloud/local_vault_sync.sh"
echo "    # or: python -m src.orchestrator.local_approval_loop --auto-pull"
echo "════════════════════════════════════════════════════════════"
