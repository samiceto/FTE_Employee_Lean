module.exports = {
  apps: [
    {
      name: 'browser-mcp',
      script: 'npx',
      args: '-y @agent-infra/mcp-server-browser --headless --host 127.0.0.1 --port 8089',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'email-mcp',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/mcp_servers/email/mcp_server_email.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        GMAIL_CREDENTIALS: '/mnt/d/FTE_Employee/hackathon_zero/src/watchers/gmail_credentials.json'
      }
    },
    {
      name: 'filesystem-watcher',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/watcher/filesystem_watcher_daemon.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero'
    },
    {
      name: 'gmail-watcher',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/watchers/gmail_watcher.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      args: '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero'
    },
    // Groq-powered AI reasoning loop - analyzes tasks and creates action plans
    // Runs every 30 minutes (1800s) with 60min cooldown
    // FREE ultra-fast inference with Llama 3.3 70B
    {
      name: 'groq-reasoning-loop',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/orchestrator/reasoning_loop.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      args: '--vault /mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault --interval 1800 --model llama-3.3-70b-versatile --min-tasks 1 --cooldown 60',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        PYTHONPATH: '/mnt/d/FTE_Employee/hackathon_zero/src'
      }
    },
    // Weekly Business Audit Watcher - generates CEO briefings every Sunday at 11 PM
    // Analyzes tasks, financials, subscriptions, and identifies bottlenecks
    // Uses Groq API (FREE) for LLM-based insights
    // Sends Slack notifications to specified channel
    {
      name: 'business-audit-watcher',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/watchers/business_audit_watcher.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      args: '--vault /mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault --day 6 --hour 23 --interval 3600 --slack-channel ' + (process.env.SLACK_DEFAULT_CHANNEL || ''),
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        PYTHONPATH: '/mnt/d/FTE_Employee/hackathon_zero/src',
        SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN,
        SLACK_DEFAULT_CHANNEL: process.env.SLACK_DEFAULT_CHANNEL
      },
      error_file: './logs/business-audit-watcher-error.log',
      out_file: './logs/business-audit-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    // Watchdog Process - monitors and restarts critical processes
    // Checks every 60 seconds and restarts crashed processes with rate limiting
    // Max 5 restarts per hour per process to prevent restart loops
    {
      name: 'watchdog',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/core/watchdog.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        PYTHONPATH: '/mnt/d/FTE_Employee/hackathon_zero',
        VAULT_PATH: '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'
      },
      error_file: './logs/watchdog-error.log',
      out_file: './logs/watchdog-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },

    // ── PLATINUM TIER: Local Approval Loop ──────────────────────────
    // Watches Pending_Approval/cloud/ for Cloud Agent drafts
    // Polls every 60s, notifies when approvals are waiting
    // Run interactively: python -m src.orchestrator.local_approval_loop
    {
      name: 'local-approval-loop',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/orchestrator/local_approval_loop.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      args: '--vault /mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault --watch --interval 60 --auto-pull',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        PYTHONPATH: '/mnt/d/FTE_Employee/hackathon_zero/src',
        VAULT_PATH: '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'
      },
      error_file: './logs/local-approval-error.log',
      out_file: './logs/local-approval-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },

    // ── PLATINUM TIER: Ralph Wiggum Loop (Execution) ─────────────────
    {
      name: 'ralph-wiggum-loop',
      script: '/mnt/d/FTE_Employee/hackathon_zero/src/orchestrator/ralph_wiggum_loop.py',
      interpreter: '/mnt/d/FTE_Employee/hackathon_zero/.venv/bin/python',
      args: '--vault /mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault --interval 300',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      cwd: '/mnt/d/FTE_Employee/hackathon_zero',
      env: {
        PYTHONPATH: '/mnt/d/FTE_Employee/hackathon_zero/src',
        VAULT_PATH: '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'
      },
      error_file: './logs/ralph-wiggum-error.log',
      out_file: './logs/ralph-wiggum-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
