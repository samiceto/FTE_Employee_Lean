// PM2 config for Cloud Agent on Azure VM
// Deploy: pm2 start ecosystem.cloud.config.js
// Note: Set APP_DIR env var or update paths below

const APP_DIR = process.env.APP_DIR || '/opt/ai_employee';
const VAULT_DIR = process.env.VAULT_DIR || `${APP_DIR}/ai_employee_vault`;
const PYTHON = `${APP_DIR}/.venv/bin/python`;

module.exports = {
  apps: [

    // ── Cloud Orchestrator (main always-on agent) ────────────────────
    {
      name: 'cloud-orchestrator',
      script: `${APP_DIR}/src/orchestrator/cloud_orchestrator.py`,
      interpreter: PYTHON,
      args: `--vault ${VAULT_DIR} --interval 300 --model llama-3.3-70b-versatile`,
      watch: false,
      autorestart: true,
      max_restarts: 20,
      restart_delay: 5000,
      cwd: APP_DIR,
      env: {
        PYTHONPATH: `${APP_DIR}/src`,
        VAULT_PATH: VAULT_DIR,
      },
      error_file: `${APP_DIR}/logs/cloud-orchestrator-error.log`,
      out_file: `${APP_DIR}/logs/cloud-orchestrator-out.log`,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },

    // ── Gmail Watcher (Cloud monitors email, triages to vault) ───────
    {
      name: 'cloud-gmail-watcher',
      script: `${APP_DIR}/src/watchers/gmail_watcher.py`,
      interpreter: PYTHON,
      args: VAULT_DIR,
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: APP_DIR,
      env: {
        PYTHONPATH: `${APP_DIR}/src`,
      },
      error_file: `${APP_DIR}/logs/cloud-gmail-error.log`,
      out_file: `${APP_DIR}/logs/cloud-gmail-out.log`,
    },

    // ── Vault Git Sync (push Cloud updates to GitHub relay) ──────────
    {
      name: 'vault-sync',
      script: `${APP_DIR}/scripts/cloud/vault_sync.sh`,
      interpreter: 'bash',
      watch: false,
      autorestart: true,
      max_restarts: 50,
      cwd: APP_DIR,
      env: {
        VAULT_PATH: VAULT_DIR,
        GIT_SYNC_INTERVAL: '60',
      },
      error_file: `${APP_DIR}/logs/vault-sync-error.log`,
      out_file: `${APP_DIR}/logs/vault-sync-out.log`,
    },

  ]
};
