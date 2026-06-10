# FTE_Employee - Quick Start Guide

**Status:** 🎉 GOLD TIER 100% COMPLETE
**Cost:** $0/month (all FREE)
**Last Updated:** Jan 25, 2026

---

## What This System Does

An autonomous AI employee that:
1. **Monitors** your emails, WhatsApp, social media
2. **Thinks** about what needs to be done (using FREE Groq AI)
3. **Plans** the work with detailed reasoning
4. **Executes** tasks automatically (Ralph Wiggum Loop)
5. **Recovers** from errors gracefully
6. **Audits** your business weekly

All while costing **$0/month**!

---

## Simple 5-Step Flow

```
📥 INPUT → 💾 STORAGE → 🧠 AI PLANS → 🤖 AUTO-EXECUTE → 📤 OUTPUT
```

### 1. INPUT (8 Watchers Collect Data)
- **Gmail Watcher** → Saves important emails
- **WhatsApp Watcher** → Saves messages
- **LinkedIn/Instagram/X/Facebook Watchers** → Post your content
- **File Watcher** → Monitors folders for new files
- **Business Audit** → Runs weekly, generates CEO briefing

### 2. STORAGE (Your Organized Vault)
```
ai_employee_vault/
├── Need_Action/     ← Tasks waiting for you
├── Approved/        ← Content ready to post
├── Plans/           ← AI-generated action plans
├── Done/            ← Completed tasks
└── Logs/audit/      ← Every operation logged
```

### 3. AI PLANS (Every 30 Minutes - FREE Groq)
**Reasoning Loop** automatically:
1. Scans `Need_Action/` for new tasks
2. Reads your `Company_Handbook.md` for context
3. Asks Groq AI: "What should I do about these tasks?"
4. Groq thinks and creates a detailed `Plan.md`
5. Saves plan with reasoning to `Plans/` folder

### 4. AUTO-EXECUTE (Ralph Wiggum Loop - Every 5 Minutes)
**Execution Engine** automatically:
1. Finds pending `Plan.md` files
2. Breaks plan into small executable tasks
3. Executes each task using the right skill
4. Monitors progress and adjusts if needed
5. Marks plan as complete when done

**Example:** Email asks for invoice →  Ralph creates invoice in Odoo → Emails it to client → Marks done!

### 5. OUTPUT (6 Automated Executors)
- **LinkedIn Watcher** → Posts automatically from `Approved/linkedin/`
- **Instagram Watcher** → Posts from `Approved/instagram/`
- **X/Twitter Watcher** → Posts from `Approved/x/`
- **Facebook Watcher** → Posts from `Approved/facebook/`
- **Email Sender** → Sends emails via SMTP
- **Odoo Accounting** → Creates invoices, tracks expenses

---

## Real Example: Email to Invoice in 15 Minutes

**9:00 AM** - Client emails: "Please send invoice for Project X"

**9:02 AM** - Gmail Watcher saves to `Need_Action/email_replies/`

**9:30 AM** - Reasoning Loop wakes up:
- Finds email task
- Asks Groq AI what to do
- Groq says: "Generate invoice, send to client"
- Creates `Plan_Invoice_Request.md`

**9:40 AM** - Ralph Wiggum Loop wakes up:
- Reads the plan
- Uses InvoiceGenerator skill (Groq parses "40 hours at $150/hour")
- Uses OdooConnector skill (creates invoice INV/2026/0042)
- Uses Email MCP (sends invoice PDF to client)
- Moves email to `Done/`

**9:45 AM** - Client receives invoice automatically!

---

## 21 Skills Available

| Skill | Uses AI? | What It Does |
|-------|----------|-------------|
| **TaskAnalyzer** | No | Scans `Need_Action/` for tasks |
| **ContextLoader** | No | Loads business context |
| **PlanGenerator** | ✅ FREE Groq | Creates action plans |
| **TaskDecomposer** | ✅ FREE Groq | Breaks plans into steps |
| **TaskSelector** | No | Picks next task to do |
| **TaskExecutor** | No | Executes individual tasks |
| **ProgressEvaluator** | ✅ FREE Groq | Checks if on track |
| **PlanAdjuster** | ✅ FREE Groq | Adjusts plan if needed |
| **OdooConnector** | No | Manages Odoo accounting |
| **InvoiceGenerator** | ✅ FREE Groq | Parses invoice requests |
| **ExpenseTracker** | ✅ FREE Groq | Parses expense receipts |
| **AccountingAggregator** | No | Financial reports |
| **FacebookAnalyzer** | ✅ FREE Groq | Analyzes FB engagement |
| **InstagramAnalyzer** | ✅ FREE Groq | Analyzes IG engagement |
| **XAnalyzer** | ✅ FREE Groq | Analyzes Twitter engagement |
| **WeeklyTaskCollector** | No | Collects completed tasks |
| **SubscriptionAuditor** | ✅ FREE Groq | Audits recurring costs |
| **BottleneckAnalyzer** | ✅ FREE Groq | Finds workflow issues |
| **CEOBriefingGenerator** | ✅ FREE Groq | Weekly business report |
| **LogAnalyzer** | No | Analyzes system logs |
| **EmailClassifier** | ✅ FREE Groq | Classifies email urgency |
| **ContentOptimizer** | ✅ FREE Groq | Optimizes social posts |

---

## How to Run Everything

### Option 1: All-in-One (PM2 - Recommended)

```bash
cd /mnt/d/FTE_Employee/hackathon_zero

# Start everything
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs
```

This starts:
- ✅ All 8 watchers
- ✅ Reasoning Loop (plans every 30 mins)
- ✅ Ralph Wiggum Loop (executes every 5 mins)
- ✅ Watchdog (monitors and restarts crashed processes)

### Option 2: Manual (For Testing)

```bash
# Just generate one plan
python -m src.orchestrator.reasoning_loop --once

# Execute a specific plan
python -m src.agents.execution_agent \
  --plan ai_employee_vault/Plans/Plan_XYZ.md

# Run single watcher
python -m src.watchers.linkedin_watcher
```

---

## Key Folders Explained

### Need_Action/ - Your Inbox
```
Need_Action/
├── email_replies/      ← Emails needing replies
├── business_tasks/     ← Manual tasks
├── social_posts/       ← Draft posts
├── whatsapp/           ← WhatsApp messages
└── failed_tasks/       ← Tasks that failed (needs your help)
```

### Approved/ - Ready to Post
```
Approved/
├── linkedin/post.md    ← LinkedIn watcher posts this
├── instagram/post.md   ← Instagram watcher posts this
├── x/post.md           ← X watcher posts this
└── facebook/post.md    ← Facebook watcher posts this
```

### Plans/ - AI Action Plans
```
Plans/
└── Plan_20260125_Invoice_Request.md   ← Created by Reasoning Loop
```

### Logs/audit/ - Everything Logged
```
Logs/audit/
└── audit_2026-01-25.jsonl   ← Every operation logged here
```

---

## What Makes It "Gold Tier"?

✅ **All Silver Features** - Basic AI planning
✅ **Odoo Accounting** - Self-hosted ERP system
✅ **Social Media** - Facebook, Instagram, X/Twitter integration
✅ **Ralph Wiggum Loop** - Autonomous task execution (the "employee" part!)
✅ **Error Recovery** - Auto-retry, queues, dead letter queue
✅ **Weekly Business Audit** - CEO briefing every Sunday
✅ **Audit Logging** - Complete audit trail of all operations
✅ **Cross-Domain** - Personal + Business together
✅ **Multiple MCP Servers** - Odoo, Email, Browser

---

## Cost Breakdown

| What | Service | Cost |
|------|---------|------|
| AI Thinking (13 skills) | Groq API | **FREE** |
| Accounting System | Odoo Community | **FREE** (self-hosted) |
| Email Monitoring | Gmail API | **FREE** |
| Social Media APIs | FB/IG/X | **FREE** |
| Browser Automation | Playwright | **FREE** (open source) |
| Everything Else | Local Python | **FREE** |
| **TOTAL** | | **$0/month** |

**You save ~$1,920/year** compared to paid alternatives!

---

## Monitoring Your System

### 1. Check Dashboard
```bash
cat ai_employee_vault/Dashboard.md
```

Shows:
- Last plan generated
- Last execution status
- Component health
- Recent alerts

### 2. View Audit Logs
```bash
# Today's events
cat ai_employee_vault/Logs/audit/audit_$(date +%Y-%m-%d).jsonl | jq

# Count event types
cat ai_employee_vault/Logs/audit/audit_*.jsonl | \
  jq -r '.event_type' | sort | uniq -c

# Find errors
cat ai_employee_vault/Logs/audit/audit_*.jsonl | \
  jq 'select(.success == false)'
```

### 3. Check System Health
```python
from src.skills.analytics.log_analyzer import LogAnalyzer
from src.skills.base_skill import SkillInput

analyzer = LogAnalyzer(vault_path='./ai_employee_vault')
result = analyzer.run(SkillInput(data={'days': 7, 'include_anomalies': True}))

print(f"Success rate: {result.result['success_rate']:.1f}%")
print(f"Total events: {result.result['total_events']}")
```

### 4. Weekly CEO Briefing
Every Sunday at 11 PM, system generates:
- Financial summary (Odoo data)
- Completed tasks
- Social media performance
- System health
- Identified bottlenecks
- Recommendations

Location: `Summaries/Weekly_Business_Audit_YYYYMMDD.md`

---

## Common Tasks

### Create a Plan Manually
```bash
# Add task to Need_Action
echo "---
type: task
priority: high
---

## Task
Send thank you email to client" > ai_employee_vault/Need_Action/business_tasks/thank_you.md

# Trigger reasoning
python -m src.orchestrator.reasoning_loop --once
```

### Post to LinkedIn
```bash
# Create approved post
echo "Just completed an amazing project! 🎉" > \
  ai_employee_vault/Approved/linkedin/announcement.md

# LinkedIn watcher will post within 60 seconds
```

### Check Odoo Invoices
```python
from src.skills.accounting.odoo_connector import OdooConnector
from src.skills.base_skill import SkillInput

odoo = OdooConnector(vault_path='./ai_employee_vault')
result = odoo.execute(SkillInput(data={
    'action': 'get_receivables'
}))

print(f"Total due: ${result.result['total_due']:.2f}")
```

### Generate Invoice (AI-Powered)
```python
from src.skills.accounting.invoice_generator import InvoiceGenerator
from src.skills.base_skill import SkillInput

gen = InvoiceGenerator(vault_path='./ai_employee_vault')
result = gen.execute(SkillInput(data={
    'description': 'Invoice ABC Corp for 10 hours consulting at $150/hour'
}))

# Groq AI parses this into structured invoice data!
print(result.result)
```

---

## Error Recovery (Automatic!)

### What Happens When Things Break?

**Scenario 1: Network Timeout**
1. Groq API times out (30 second limit)
2. Retry handler catches it
3. Waits 1 second, retries
4. If fails again, waits 2 seconds, retries
5. If still fails, waits 4 seconds, final retry
6. If all fail → Task goes to Dead Letter Queue
7. Creates `failed_tasks/task_xyz.md` for human review
8. Notifier sends Slack alert (if configured)

**Scenario 2: Process Crashes**
1. Ralph Wiggum Loop crashes
2. Watchdog detects missing PID file (checks every 60s)
3. Watchdog restarts the process automatically
4. Sends alert notification
5. Logs watchdog_restart event
6. Rate limit: Max 5 restarts per hour

**Scenario 3: Odoo Offline**
1. Invoice creation fails (Odoo unreachable)
2. Task marked as failed
3. Added to TaskQueue (30-day retention)
4. Health Monitor marks Odoo as OFFLINE
5. System continues operating (graceful degradation)
6. When Odoo comes back, queue is processed

---

## Troubleshooting

### No Plans Generated?
```bash
# 1. Check tasks exist
ls ai_employee_vault/Need_Action/**/*.md

# 2. Check reasoning loop running
pm2 list | grep reasoning

# 3. Check Groq API key
echo $GROQ_API_KEY

# 4. Run manually with verbose
python -m src.orchestrator.reasoning_loop --once --verbose
```

### Ralph Not Executing?
```bash
# 1. Check plans exist
ls ai_employee_vault/Plans/*.md

# 2. Check loop running
pm2 list | grep ralph

# 3. Execute manually
python -m src.agents.execution_agent \
  --plan ai_employee_vault/Plans/Plan_XYZ.md \
  --verbose
```

### Social Media Not Posting?
```bash
# 1. Check approved content exists
ls ai_employee_vault/Approved/linkedin/*.md

# 2. Check watcher logs
pm2 logs linkedin-watcher

# 3. Verify session
ls linkedin_user_data/
```

---

## Configuration (.env file)

```bash
# Required
GROQ_API_KEY=your_free_key_here
VAULT_PATH=/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault

# LinkedIn (if using)
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password

# Odoo (if using)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=your_odoo_password

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/... (for alerts)
ADMIN_EMAIL=admin@example.com (for critical alerts)
```

---

## System Status Check

```bash
# All services running?
pm2 status

# Recent activity?
tail -n 50 ai_employee_vault/Logs/audit/audit_$(date +%Y-%m-%d).jsonl

# Any errors?
cat ai_employee_vault/Logs/audit/audit_*.jsonl | \
  jq 'select(.success == false)' | tail -n 10

# Queue sizes?
ls -lh ai_employee_vault/Queue/emails/
ls -lh ai_employee_vault/Queue/tasks/
ls -lh ai_employee_vault/Queue/dead_letter/

# Component health?
cat ai_employee_vault/Health/component_health.json | jq
```

---

## What You Get

**21 AI Skills** - From planning to execution to analysis
**8 Watchers** - Monitor everything automatically
**2 Orchestrators** - Planning + Execution engines
**3 MCP Servers** - Odoo, Email, Browser integration
**7 Core Modules** - Error recovery, monitoring, alerts
**1 Audit System** - Complete observability
**Weekly CEO Briefing** - Business intelligence
**$0/month Cost** - All FREE services

---

## Next Steps

1. **Deploy Everything**
   ```bash
   pm2 start ecosystem.config.js
   pm2 save
   ```

2. **Monitor for 1 Week**
   - Check dashboard daily
   - Review audit logs
   - Read CEO briefing (Sundays)
   - Verify error recovery works

3. **Enjoy Your AI Employee!**
   - It monitors your channels
   - It thinks about tasks
   - It creates plans
   - It executes autonomously
   - It recovers from errors
   - It audits your business
   - **All for $0/month!**

---

**Status:** 🎉 **Production Ready!**
**Your autonomous AI employee is complete and operational.**

Get free Groq API key: https://console.groq.com/keys
