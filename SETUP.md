# 🚀 Setup Guide — Running FTE_Employee After Cloning

This guide walks you through getting the project running from a fresh clone.

> ⚠️ **Secrets are NOT in this repo.** All API keys, OAuth tokens, and credentials are
> git-ignored. The placeholders below show you *what* to fill in. Replace
> every `your_...` / `<...>` value with your real one. (If this is your own machine, keep
> your real values in a local, git-ignored notes file — never commit them.)

---

## 1. Prerequisites

- **Python 3.12+**
- **Node.js 20+** (for the dashboard)
- **uv** (recommended) or pip
- **Docker** (only if you want the cloud Odoo stack)
- A **Groq API key** (free): https://console.groq.com/keys

---

## 2. Clone & install backend

```bash
git clone https://github.com/samiceto/FTE_Employee.git
cd FTE_Employee

# create venv + install deps
uv sync                 # or: python -m venv .venv && source .venv/bin/activate && pip install -e .
```

---

## 3. Create the root `.env`

Create a file named `.env` in the project root with these keys:

```dotenv
# ---- LLM provider ----
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key            # https://console.groq.com/keys

# Optional alternative providers
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
DASHSCOPE_API_KEY=sk-your-dashscope-key-here
OLLAMA_HOST=http://localhost:11434

# ---- Email MCP server (sending replies via SMTP) ----
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password    # 16-char Gmail App Password, NOT your login password

# ---- Odoo (accounting integration) ----
ODOO_URL=http://localhost:8069
ODOO_DB=your_odoo_db_name
ODOO_USER=your_odoo_admin_email
ODOO_PASSWORD=your_odoo_admin_password

# ---- Slack (optional) ----
SLACK_BOT_TOKEN=xoxb-your-bot-token        # Slack app → OAuth & Permissions
SLACK_APP_TOKEN=xapp-your-app-token        # Slack app → Basic Information → App-Level Tokens
SLACK_TEAM_ID=your_team_id
SLACK_DEFAULT_CHANNEL=your_channel_id
```

---

## 4. Set up Gmail API access

The Gmail watcher needs an OAuth client + a token. Neither is in the repo.

1. Go to https://console.cloud.google.com/ → create a project (or reuse one).
2. **APIs & Services → Library →** enable **Gmail API**.
3. **Credentials → Create Credentials → OAuth client ID → Desktop app.**
4. Download the JSON and save it as:
   ```
   src/watchers/gmail_credentials.json
   ```
   It should look like:
   ```json
   {"installed":{"client_id":"your_client_id.apps.googleusercontent.com",
   "project_id":"your_project_id","auth_uri":"https://accounts.google.com/o/oauth2/auth",
   "token_uri":"https://oauth2.googleapis.com/token",
   "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
   "client_secret":"your_client_secret","redirect_uris":["http://localhost"]}}
   ```
5. Generate the access token (opens a browser consent screen once):
   ```bash
   .venv/bin/python src/watchers/generate_token.py
   ```
   This creates `src/watchers/token.json` automatically. Re-run it if the token expires.

---

## 5. Run the system

> **No browser logins needed.** This build uses only official APIs (Gmail, Odoo, Groq,
> Slack) — there are no Playwright/browser watchers to set up.

**Reasoning loop (the brain):**
```bash
python -m src.orchestrator.reasoning_loop --once          # single pass
python -m src.orchestrator.reasoning_loop --interval 1800 # every 30 min
```

**Gmail watcher:**
```bash
python -m src.watchers.gmail_watcher
```

**All services via PM2 (optional):**
```bash
pm2 start ecosystem.config.js
```
> The PM2 config uses absolute `/mnt/d/FTE_Employee/...` paths — edit them to match your
> clone location first.

---

## 6. Run the dashboard (frontend)

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

> Note: the dashboard currently renders from `frontend/lib/mock-data.ts` (placeholder data).
> It is not yet wired to the live vault/backend.

---

## 7. (Optional) Cloud Odoo stack

```bash
cd cloud
cp ../.env.cloud.example .env      # fill in real values
docker compose up -d
./certbot-init.sh                  # HTTPS via Let's Encrypt (after DNS points to the VM)
```

---

## 8. Vault structure

`ai_employee_vault/` is the file-based workflow. The repo ships the **empty folder structure**
(via `.gitkeep`); real data is generated at runtime. Key folders:

| Folder | Purpose |
|--------|---------|
| `Inbox/` | Raw incoming items (gmail) |
| `Need_Action/` | Tasks awaiting reasoning |
| `Pending_Approval/` | AI drafts awaiting your approval |
| `Approved/` | Approved items ready to act on |
| `Done/` | Completed items |
| `Plans/` | AI-generated action plans |
| `Logs/` | Reasoning + audit logs |

---

## Quick reference — files you must create (not in repo)

| File | Purpose | How |
|------|---------|-----|
| `.env` | All secrets/config | §3 |
| `src/watchers/gmail_credentials.json` | Gmail OAuth client | §4 |
| `src/watchers/token.json` | Gmail OAuth token | §4 (`generate_token.py`) |
| `.venv/` | Python env | §2 (`uv sync`) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not found` | Add it to `.env` (§3). |
| Gmail auth fails | Re-run `generate_token.py`; check `gmail_credentials.json` exists. |
| Odoo connection fails | Verify `ODOO_URL`/`ODOO_DB`/`ODOO_USER`/`ODOO_PASSWORD` in `.env`. |
