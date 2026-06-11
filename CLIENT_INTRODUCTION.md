# Meet Your AI Employee

### An autonomous back-office assistant that reads your email, keeps your books, plans your work, and briefs you like a chief of staff — for $0/month in AI costs.

---

## 1. What is this?

**FTE AI Employee** is a software system that behaves like a diligent full-time back-office employee. It watches your business inputs around the clock, thinks about what needs to be done, drafts the work, and waits for your one-click approval before anything goes out the door.

Think of it as hiring someone who:

- **Never sleeps** — monitors your Gmail inbox and business metrics 24/7.
- **Never forgets** — every task, draft, and decision is written to disk as a readable file you can open and audit.
- **Never acts without permission** — anything customer-facing (an email reply, an invoice) sits in a *Pending Approval* folder until you approve it.
- **Costs almost nothing to run** — the AI reasoning layer runs on Groq's free tier (Llama 3.3 70B); Gmail and Odoo APIs are free.

---

## 2. What does it actually do?

| Capability | What happens in practice |
|------------|--------------------------|
| 📧 **Email triage & reply drafting** | Reads incoming Gmail, classifies each message (urgent / client request / noise), and drafts a context-aware reply for your approval. |
| 💰 **Accounting on autopilot** | Creates invoices, records expenses, and pulls accounts-receivable and financial reports directly in **Odoo** (a full ERP) via XML-RPC. |
| 🧠 **Task reasoning & planning** | Every 30 minutes it gathers all pending tasks, breaks them into steps, and produces a prioritized, human-readable action plan. |
| 📊 **Executive analytics** | Generates CEO briefings, finds operational bottlenecks, audits recurring subscriptions for waste, and analyzes its own logs. |
| 🖥️ **Control dashboard** | A modern web dashboard (Next.js) where you watch agents work, review approvals, and inspect every audit log entry. |

---

## 3. How it works — the pipeline

The system is organized as a five-stage pipeline. Data flows left to right, and a human approval gate sits in front of every outward-facing action.

```
  INPUTS                 STORAGE              REASONING              APPROVAL              OUTPUTS
┌──────────────┐    ┌───────────────┐    ┌────────────────┐    ┌───────────────┐    ┌────────────────┐
│ Gmail Watcher │    │  The "Vault"  │    │  Reasoning Loop │    │  Human Gate   │    │ Email (MCP)    │
│ (polls inbox) │───►│  Inbox/       │───►│  every 30 min:  │───►│ Pending_      │───►│ Odoo invoices  │
│               │    │  Need_Action/ │    │  • analyze tasks│    │ Approval/     │    │ & expenses     │
│ Business Audit│    │  Plans/       │    │  • load context │    │      ↓        │    │ CEO briefings  │
│ Watcher       │    │  Done/        │    │  • generate plan│    │  you approve  │    │ Action plans   │
│ (metrics)     │    │  Logs/        │    │  (Groq Llama 3.3)│   │  with 1 click │    │ Audit reports  │
└──────────────┘    └───────────────┘    └────────────────┘    └───────────────┘    └────────────────┘
```

### Step by step

1. **Input — where work comes from.** Two watchers feed the system: the **Gmail Watcher** polls your inbox through the official Google API (OAuth2 — no password scraping), and the **Business Audit Watcher** monitors operational metrics on a schedule. Each new item becomes a markdown task file in the vault.

2. **Storage — the vault.** Everything lives in a plain-folder workflow (`Inbox/ → Need_Action/ → Pending_Approval/ → Approved/ → Done/`). No black box: you can open any file at any moment and read exactly what the AI saw, thought, and proposed.

3. **Reasoning — the brain.** Every 30 minutes the orchestrator wakes up, scans pending tasks, loads your business context (company handbook, business goals), and asks the AI to produce a prioritized **action plan** — a readable markdown document with numbered steps, effort estimates, and which skill executes each step.

4. **Approval — the safety gate.** Drafted replies and invoices land in `Pending_Approval/`. Nothing is sent, posted, or booked until you move it to `Approved/` — from the dashboard or the file system. You stay in control; the AI does the typing.

5. **Output — the hands.** Approved work executes through dedicated connectors: email goes out through an MCP email server, accounting entries are written to Odoo, and analytics reports (CEO briefing, bottleneck analysis, subscription audit) are generated as documents.

Every single operation — success or failure — is written to an **audit log**, and failed operations are retried automatically with a dead-letter queue for anything that needs human eyes.

---

## 4. System design

The codebase is deliberately modular — built around small, single-purpose **skills** that an agent composes into workflows.

```
hackathon_zero/
├── src/
│   ├── skills/            ← 20+ modular skills (the "abilities")
│   │   ├── analysis/        task_analyzer, context_loader
│   │   ├── planning/        plan_generator (AI)
│   │   ├── communication/   email_classifier (AI)
│   │   ├── execution/       task_decomposer, selector, executor, progress_evaluator
│   │   ├── accounting/      invoice_generator, expense_tracker, odoo_connector
│   │   └── analytics/       ceo_briefing, bottleneck_analyzer, subscription_auditor
│   ├── agents/            ← orchestration: composes skills into behaviour
│   ├── watchers/          ← gmail_watcher, business_audit_watcher (the "senses")
│   ├── mcp_servers/       ← email + Odoo connectors (the "hands")
│   └── orchestrator/      ← reasoning_loop (the "heartbeat", runs every 30 min)
├── frontend/              ← Next.js dashboard (the "window" into the system)
├── ai_employee_vault/     ← file-based task pipeline (the "memory")
└── cloud/                 ← Docker deployment stack (Postgres + Odoo + Nginx + SSL)
```

**Key design decisions and why they matter to you:**

- **Skills, not monolith.** Each ability (classify an email, create an invoice, audit subscriptions) is an independent module. Adding a new capability means adding one file — not rewriting the system.
- **Files, not databases, for the workflow.** Tasks and plans are markdown files. That makes the entire decision trail human-readable, version-controllable, and recoverable — a business owner can audit the AI with a file explorer.
- **Human-in-the-loop by architecture, not by promise.** The approval gate is a physical folder boundary. The execution layer simply cannot see a draft until it's been moved to `Approved/`.
- **Resilience built in.** Automatic retries with exponential backoff, a dead-letter queue for persistent failures, graceful degradation when an external service is down, and full audit logging on every operation.
- **Cloud-ready.** Ships with a Docker Compose stack (Odoo + PostgreSQL + Nginx + automatic SSL certificates) and PM2 process definitions for one-command deployment.

---

## 5. Inputs and outputs at a glance

| It takes in… | It produces… |
|--------------|--------------|
| Incoming Gmail messages (official API) | Classified email + drafted replies (sent only after your approval) |
| Your business context (handbook, goals) | Prioritized, step-by-step action plans |
| Pending tasks accumulated in the vault | Decomposed sub-tasks with effort estimates and execution status |
| Invoice / expense requests | Real invoices and expense records inside Odoo, plus AR reports |
| Operational metrics & its own logs | CEO briefings, bottleneck analyses, subscription waste audits |
| Every action it performs | A permanent, searchable audit trail |

---

## 6. What value does this add to your business?

### Reclaim hours, every single day
Email triage, invoice creation, expense entry, and status reporting are the classic "death by a thousand cuts" of small-business operations — typically **2–4 hours per day** of founder or admin time. The AI Employee does the reading, drafting, and bookkeeping; you spend seconds approving instead of hours producing.

### Near-zero running cost
The reasoning layer runs on **Groq's free tier**. Gmail and Odoo APIs are free. Compare that with a part-time back-office hire or a stack of per-seat SaaS subscriptions — this system's marginal cost is effectively the electricity to run it.

### Nothing falls through the cracks
Every email becomes a tracked task with a lifecycle. Every task ends in `Done/` or surfaces in an exception queue. The 30-minute reasoning cycle means nothing sits unnoticed for longer than half an hour.

### Decisions you can audit
Unlike a chat assistant, every recommendation comes with written reasoning ("*per the company handbook, invoices go out within 24 hours; Project X shows 40 hours at $150/h*") stored in a file. If a regulator, accountant, or co-founder asks "why did the system do that?" — the answer is on disk.

### Executive visibility without the meetings
The weekly CEO briefing and bottleneck analysis turn raw operational exhaust (logs, task throughput, spending) into a readable executive summary. The subscription auditor alone routinely pays for the setup time by flagging forgotten recurring charges.

### Safe by design
- Customer-facing actions require **explicit human approval** — always.
- Credentials are stored locally in environment files, never in code.
- Gmail access uses Google's official OAuth flow with revocable tokens.
- The complete audit log means full accountability for every action taken.

---

## 7. Seeing it live

The **control dashboard** is the easiest way to experience the system: a real-time view of every agent, the task queue, pending approvals, email activity, analytics, and audit logs — all in a polished dark interface designed for at-a-glance operation.

```bash
cd frontend && npm install && npm run dev   # → http://localhost:3000
```

Full setup (Gmail OAuth, Odoo, environment variables) is documented step-by-step in **[SETUP.md](SETUP.md)**.

---

*FTE AI Employee — hire your first employee that works around the clock, documents everything, and never asks for a raise.*
