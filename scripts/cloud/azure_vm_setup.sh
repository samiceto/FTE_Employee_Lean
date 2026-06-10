#!/usr/bin/env bash
# Azure VM One-Shot Setup Script
# Run this ONCE on a fresh Azure B1s Ubuntu 22.04 VM:
#   chmod +x azure_vm_setup.sh && sudo ./azure_vm_setup.sh
#
# What it does:
#   1. Adds 2GB swap (critical for B1s 1GB RAM + Odoo)
#   2. Installs: Docker, Docker Compose, Python 3.12, PM2, git
#   3. Clones your vault repo
#   4. Sets up Cloud Agent + Odoo as PM2 services
#   5. Configures UFW firewall (80, 443, 22 only)
#
# Prerequisites:
#   - Azure B1s VM (Ubuntu 22.04 LTS)
#   - Open ports 80, 443, 22 in Azure Network Security Group
#   - GitHub repo for vault sync (set VAULT_REPO_URL below)
#   - .env file ready to upload (scp .env user@vm:/opt/ai_employee/.env)

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
VAULT_REPO_URL="${VAULT_REPO_URL:-}"          # e.g. git@github.com:you/vault.git
APP_DIR="/opt/ai_employee"
VAULT_DIR="/opt/ai_employee_vault"
PYTHON_VERSION="3.12"
NODE_VERSION="20"
DOMAIN="${DOMAIN:-}"                           # e.g. myai.eastus.cloudapp.azure.com

# ── Colors ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[SETUP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

[[ $EUID -eq 0 ]] || err "Run as root: sudo ./azure_vm_setup.sh"
log "Starting Azure VM setup for AI Employee Platinum Tier..."

# ── 1. Swap (2GB) ─────────────────────────────────────────────────────
log "Setting up 2GB swap..."
if ! swapon --show | grep -q /swapfile; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    # Tune swappiness for server workload
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    sysctl -p
    log "Swap created: 2GB"
else
    log "Swap already exists — skipping"
fi

# ── 2. System packages ─────────────────────────────────────────────────
log "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    curl git wget unzip htop \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip \
    ca-certificates gnupg lsb-release ufw

# ── 3. Docker ─────────────────────────────────────────────────────────
log "Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "${SUDO_USER:-ubuntu}"
    log "Docker installed"
else
    log "Docker already installed"
fi

# Docker Compose plugin
if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi

# ── 4. Node.js + PM2 ──────────────────────────────────────────────────
log "Installing Node.js ${NODE_VERSION} + PM2..."
if ! command -v node &>/dev/null; then
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash -
    apt-get install -y -qq nodejs
fi
npm install -g pm2 --quiet
pm2 startup systemd -u "${SUDO_USER:-ubuntu}" --hp "/home/${SUDO_USER:-ubuntu}"

# ── 5. Python venv for Cloud Agent ───────────────────────────────────
log "Creating Python virtual environment..."
mkdir -p "${APP_DIR}"
python${PYTHON_VERSION} -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install -q --upgrade pip

# ── 6. Clone / update vault repo ─────────────────────────────────────
if [[ -n "${VAULT_REPO_URL}" ]]; then
    log "Cloning vault from ${VAULT_REPO_URL}..."
    if [[ -d "${APP_DIR}/.git" ]]; then
        git -C "${APP_DIR}" pull --rebase origin main
    else
        git clone "${VAULT_REPO_URL}" "${APP_DIR}"
    fi
    # Install Python deps
    if [[ -f "${APP_DIR}/pyproject.toml" ]]; then
        "${APP_DIR}/.venv/bin/pip" install -q -e "${APP_DIR}[cloud]" 2>/dev/null || \
        "${APP_DIR}/.venv/bin/pip" install -q groq python-dotenv
    fi
    # Create vault directory symlink
    ln -sfn "${APP_DIR}/ai_employee_vault" "${VAULT_DIR}" 2>/dev/null || true
else
    warn "VAULT_REPO_URL not set — clone your repo manually to ${APP_DIR}"
fi

# ── 7. Firewall (UFW) ─────────────────────────────────────────────────
log "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
log "Firewall: SSH(22), HTTP(80), HTTPS(443) open"

# ── 8. Deploy Odoo Docker stack ───────────────────────────────────────
if [[ -f "${APP_DIR}/cloud/docker-compose.yml" ]]; then
    log "Starting Odoo Docker stack..."
    cd "${APP_DIR}/cloud"
    docker compose up -d
    log "Odoo starting (may take 60s on first run)..."
else
    warn "cloud/docker-compose.yml not found — run after cloning repo"
fi

# ── 9. PM2 Cloud Agent service ────────────────────────────────────────
if [[ -f "${APP_DIR}/cloud/ecosystem.cloud.config.js" ]]; then
    log "Starting Cloud Agent via PM2..."
    su - "${SUDO_USER:-ubuntu}" -c "pm2 start ${APP_DIR}/cloud/ecosystem.cloud.config.js"
    su - "${SUDO_USER:-ubuntu}" -c "pm2 save"
    log "Cloud Agent PM2 services started"
else
    warn "ecosystem.cloud.config.js not found — start manually after deploy"
fi

# ── 10. HTTPS setup reminder ──────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Upload your .env file:"
echo "     scp .env ubuntu@<VM_IP>:${APP_DIR}/.env"
echo ""
echo "  2. Set your domain in nginx config:"
echo "     Edit: ${APP_DIR}/cloud/nginx/conf.d/odoo.conf"
echo "     Replace YOUR_DOMAIN_OR_IP with your Azure DNS name"
echo ""
echo "  3. Obtain HTTPS certificate:"
echo "     cd ${APP_DIR}/cloud && ./certbot-init.sh YOUR_DOMAIN YOUR_EMAIL"
echo ""
echo "  4. Access Odoo:"
echo "     https://YOUR_DOMAIN (after cert) or http://<VM_IP>"
echo ""
if [[ -n "${DOMAIN}" ]]; then
    echo "  Azure DNS: ${DOMAIN}"
    echo "  Odoo URL: https://${DOMAIN}"
fi
echo "════════════════════════════════════════════════════════════"
