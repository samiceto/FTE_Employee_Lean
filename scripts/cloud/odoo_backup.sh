#!/usr/bin/env bash
# Odoo Cloud Backup Script
# Backs up Odoo database to /opt/backups/odoo/
# Schedule via cron: 0 2 * * * /opt/ai_employee/scripts/cloud/odoo_backup.sh

set -euo pipefail

BACKUP_DIR="/opt/backups/odoo"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${ODOO_DB:-odoo}"
DB_USER="${ODOO_DB_USER:-odoo}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [odoo-backup] $*"; }

mkdir -p "${BACKUP_DIR}"

log "Starting Odoo backup..."

# Database dump via Docker
docker exec odoo_db pg_dump \
    -U "${DB_USER}" \
    "${DB_NAME}" \
    | gzip > "${BACKUP_DIR}/odoo_db_${TIMESTAMP}.sql.gz"

# Odoo filestore
tar -czf "${BACKUP_DIR}/odoo_filestore_${TIMESTAMP}.tar.gz" \
    -C /var/lib/docker/volumes/cloud_odoo_data/_data . 2>/dev/null || \
docker run --rm \
    -v cloud_odoo_data:/data \
    -v "${BACKUP_DIR}:/backup" \
    alpine tar -czf "/backup/odoo_filestore_${TIMESTAMP}.tar.gz" -C /data .

log "Backup complete: odoo_db_${TIMESTAMP}.sql.gz"

# Cleanup old backups
find "${BACKUP_DIR}" -name "*.gz" -mtime "+${KEEP_DAYS}" -delete
log "Cleaned up backups older than ${KEEP_DAYS} days"

# Log backup to vault
VAULT_PATH="${VAULT_PATH:-/opt/ai_employee_vault}"
UPDATES_DIR="${VAULT_PATH}/Updates/cloud"
mkdir -p "${UPDATES_DIR}"
echo "---
agent: odoo_backup
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
type: backup_report
---

## Odoo Backup — $(date -u '+%Y-%m-%d %H:%M UTC')

| Field | Value |
|-------|-------|
| Status | ✅ Success |
| DB backup | odoo_db_${TIMESTAMP}.sql.gz |
| Retention | ${KEEP_DAYS} days |
" > "${UPDATES_DIR}/backup_${TIMESTAMP}.md"

log "Done."
