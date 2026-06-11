# FTE_Employee (Lean) — AI Back-Office Assistant

A modular, skill-based AI assistant that handles back-office work: it triages and drafts
email replies, keeps your books in Odoo, reasons over pending tasks to produce action plans,
and generates business analytics — all surfaced through a Next.js dashboard.

> **This is the "lean" build.** Social-media browser automation (LinkedIn / X / Instagram /
> Facebook) has been removed in favour of the deployable, API-based core. See
> [`FTE_Employee`](https://github.com/samiceto/FTE_Employee) for the full original version.

---

## What it does

| Capability | How |
|------------|-----|
| 📧 **Email triage & reply** | Reads Gmail (official API), classifies messages, drafts replies; sends via the email MCP server. |
| 💰 **Accounting** | Creates invoices, records expenses, and reports AR/financials in Odoo via XML-RPC. |
| 🧠 **Task reasoning** | Collects pending tasks, decomposes them, and generates prioritized action plans with Groq (Llama 3.3 70B). |
| 📊 **Business analytics** | CEO briefings, bottleneck analysis, subscription audits, and log analysis. |
| 🖥️ **Dashboard** | Next.js 16 UI to review tasks, approvals, email, analytics, logs, and settings. |

**Cost:** the reasoning layer runs on Groq's free tier ($0). Gmail and Odoo APIs are free.

---

## Architecture

```
hackathon_zero/
├── src/
│   ├── skills/                     # Modular skill system
│   │   ├── base_skill.py           # Base class + Groq integration
│   │   ├── registry.py             # Skill discovery & registration
│   │   ├── analysis/               # task_analyzer, context_loader
│   │   ├── planning/               # plan_generator (Groq)
│   │   ├── content/                # content_optimizer (Groq)
│   │   ├── communication/          # email_classifier (Groq)
│   │   ├── execution/              # task_decomposer/selector/executor, plan_adjuster, progress_evaluator
│   │   ├── accounting/             # invoice_generator, expense_tracker, accounting_aggregator, odoo_connector
│   │   └── analytics/              # ceo_briefing_generator, bottleneck_analyzer, subscription_auditor, log_analyzer, weekly_task_collector
│   │
│   ├── agents/                     # Agent orchestration
│   ├── watchers/                   # gmail_watcher, business_audit_watcher
│   ├── mcp_servers/                # email + odoo MCP servers
│   └── orchestrator/               # reasoning_loop (main loop)
│
├── frontend/                       # Next.js 16 dashboard (currently mock data)
├── ai_employee_vault/              # File-based workflow (structure only; data is git-ignored)
├── cloud/                          # Docker Odoo stack (Postgres + Odoo + Nginx + certbot)
├── ecosystem.config.js             # PM2 process definitions
├── SETUP.md                        # Full clone-to-run instructions
└── README.md                       # This file
```

---

## Quick start

> Full step-by-step instructions (env vars, Gmail OAuth, Odoo, etc.) are in **[SETUP.md](SETUP.md)**.

```bash
# 1. Install
uv sync                       # or: python -m venv .venv && pip install -e .

# 2. Configure
cp .env.example .env          # then fill in GROQ_API_KEY, email, and Odoo values

# 3. Run the reasoning loop
python -m src.orchestrator.reasoning_loop --once          # single pass
python -m src.orchestrator.reasoning_loop --interval 1800 # every 30 min

# 4. Run the Gmail watcher
python -m src.watchers.gmail_watcher

# 5. Dashboard
cd frontend && npm install && npm run dev   # http://localhost:3000
```

Or start everything with PM2:

```bash
pm2 start ecosystem.config.js   # edit the absolute paths inside first
```

---

## The vault workflow

`ai_employee_vault/` is a file-based pipeline. The repo ships the empty folder structure;
real data is generated at runtime and git-ignored.

| Folder | Purpose |
|--------|---------|
| `Inbox/` | Raw incoming items (gmail) |
| `Need_Action/` | Tasks awaiting reasoning |
| `Pending_Approval/` | AI drafts awaiting your approval |
| `Approved/` | Approved items ready to act on |
| `Done/` | Completed items |
| `Plans/` | AI-generated action plans |
| `Accounting/` | Invoices, expenses, financial summaries |
| `Briefings/` | CEO briefings & analytics reports |
| `Logs/` | Reasoning + audit logs |

**Flow:** watchers drop items in `Inbox`/`Need_Action` → the reasoning loop analyzes them and
writes a plan → drafts land in `Pending_Approval` → you approve → results move to `Done`.

---

## Skills

The system is built from discrete, auto-discovered skill classes. Add one by dropping a file
into the right `src/skills/<category>/` folder:

```python
from ..base_skill import BaseSkill, SkillInput, SkillOutput

class MySkill(BaseSkill):
    SKILL_NAME = "my_skill"
    REQUIRES_LLM = False        # True to use Groq
    DESCRIPTION = "What this skill does"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        return SkillOutput(result="data", success=True)
```

The `SkillRegistry` auto-discovers it — no registration needed.

---

## Testing

```bash
pytest                      # all tests
pytest tests/skills/ -v     # skill tests
```

---

## Dashboard status

The Next.js dashboard currently renders from `frontend/lib/mock-data.ts` (placeholder data);
it is not yet wired to the live vault/backend. Wiring the **Approvals** and **Tasks** pages to
real vault data is the natural next step.

---

## Cloud (optional)

`cloud/docker-compose.yml` stands up Odoo + PostgreSQL + Nginx (HTTPS via Let's Encrypt) on a
small VM:

```bash
cd cloud
cp ../.env.cloud.example .env   # fill in real values
docker compose up -d
./certbot-init.sh               # after DNS points at the VM
```

---

## Notes & roadmap

- **No browser automation.** Every integration uses an official API (Gmail, Odoo XML-RPC,
  Groq, Slack) — nothing drives a headless browser, so there are no platform-ToS or
  account-ban risks and it deploys cleanly to a normal server.
- Messaging/social channels (WhatsApp, Instagram, Facebook, X, LinkedIn) were removed; any of
  them could be reintroduced later via their **official APIs** rather than browser automation.
- Planned: wire the dashboard to the real backend; add a small API layer over the vault.

---

## License

MIT
