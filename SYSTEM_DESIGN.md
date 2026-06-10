# FTE_Employee - System Design & Data Flow

## Project Overview
An AI-powered autonomous employee system that monitors multiple channels (Gmail, LinkedIn, Instagram, X/Twitter, WhatsApp), collects tasks, uses AI to create action plans, and automatically executes approved tasks. Built with a modular skill-based architecture using FREE Groq API ($0/month).

---

## System Architecture (Tiered Implementation)

### Bronze Tier (Foundation)
- Obsidian vault for data storage
- Basic file monitoring
- Manual task processing

### Silver Tier (Current - Functional Assistant)
- Multiple channel watchers
- AI reasoning with modular skills
- Automated LinkedIn posting
- Human-in-the-loop approvals

### Gold Tier (Autonomous Employee)
- Full cross-domain integration
- Odoo accounting integration
- Multi-platform social media
- Error recovery & audit logging
- Ralph Wiggum autonomous loop

---

## Data Flow: Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT SOURCES (Watchers)                    │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─► Gmail Watcher          → emails → Need_Action/email_replies/
    ├─► WhatsApp Watcher       → messages → Need_Action/whatsapp/
    ├─► File System Watcher    → files → Need_Action/business_tasks/
    └─► Manual Input           → tasks → Need_Action/social_posts/

                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA STORAGE (Vault)                          │
│  ai_employee_vault/                                              │
│  ├── Need_Action/        ← Pending tasks collected here          │
│  ├── Approved/          ← Human-approved content for posting    │
│  ├── Plans/             ← AI-generated action plans             │
│  ├── Done/              ← Completed tasks archived here         │
│  └── Logs/              ← AI reasoning & audit logs             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                AI REASONING ENGINE (Skills System)               │
│                                                                  │
│  Orchestrator (reasoning_loop.py)                               │
│  ├─► Every 30 mins, checks Need_Action folder                   │
│  └─► Triggers ReasoningAgent if tasks found                     │
│                                                                  │
│  ReasoningAgent (reasoning_agent.py)                            │
│  ├─► Step 1: TaskAnalyzer Skill                                │
│  │   └─ Scans Need_Action/, parses markdown → TaskItem[]       │
│  │                                                              │
│  ├─► Step 2: ContextLoader Skill                               │
│  │   └─ Loads Company_Handbook.md + Business_Goals.md          │
│  │                                                              │
│  └─► Step 3: PlanGenerator Skill (Groq AI)                     │
│      └─ Sends tasks + context to Groq Llama 3.3 70B            │
│      └─ Groq reasons → generates Plan.md                       │
│      └─ Saves to Plans/ folder                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PLAN.MD STRUCTURE                             │
│                                                                  │
│  ---                                                             │
│  title: "Task Summary"                                          │
│  created: 2026-01-25T10:30:00                                   │
│  complexity: moderate                                           │
│  status: pending                                                │
│  ---                                                             │
│                                                                  │
│  ## Summary                                                      │
│  Brief overview of what needs to be done                        │
│                                                                  │
│  ## Reasoning                                                    │
│  AI's thought process and justification                         │
│                                                                  │
│  ## Action Steps                                                 │
│  ### Step 1: [Action Title]                                     │
│  - Assignee: 🤖 automated / 🤝 hybrid / 👤 human               │
│  - Effort: low/medium/high                                      │
│  - Related Tasks: [task files]                                  │
│  [Detailed instructions]                                         │
│                                                                  │
│  ## Risks                                                        │
│  ## Success Criteria                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                 HUMAN APPROVAL (Manual Step)                     │
│  Human reviews Plan.md and:                                      │
│  1. Creates approved content in Approved/ folders               │
│  2. Moves tasks from Need_Action/ if handling manually          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                OUTPUT EXECUTORS (Watchers)                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ├─► LinkedIn Watcher    → Checks Approved/linkedin/
    │                        → Posts to LinkedIn via Playwright
    │                        → Moves to Done/
    │
    ├─► Instagram Watcher   → Checks Approved/instagram/
    │                        → Posts to Instagram
    │                        → Moves to Done/
    │
    └─► X/Twitter Watcher   → Checks Approved/x/
                             → Posts to Twitter
                             → Moves to Done/
```

---

## Component Roles & Responsibilities

### 1. WATCHERS (Input Collectors)
**Location:** `src/watchers/`

#### Gmail Watcher (`gmail_watcher.py`)
- **Input:** Gmail API (OAuth2 authenticated)
- **Trigger:** Polls every 2 minutes for unread important emails
- **Process:**
  1. Fetches unread emails using Gmail API
  2. Extracts headers (From, Subject, Date)
  3. Creates markdown file with YAML frontmatter
- **Output:** `Need_Action/email_replies/EMAIL_{id}.md`

#### LinkedIn Watcher (`linkedin_watcher.py`)
- **Input:** Scans `Approved/linkedin/` folder
- **Trigger:** Polls every 60 seconds
- **Process:**
  1. Reads markdown files with content + image_path
  2. Uses Playwright to automate LinkedIn posting
  3. Handles login session persistence
- **Output:** Posts live to LinkedIn, moves files to `Done/`

#### Similar Pattern for:
- WhatsApp Watcher → monitors messages
- Instagram Watcher → posts to Instagram
- X/Twitter Watcher → posts to Twitter
- Facebook Watcher → posts to Facebook

---

### 2. REASONING ENGINE (AI Brain)

#### Orchestrator (`src/orchestrator/reasoning_loop.py`)
- **Role:** Scheduler and coordinator
- **Trigger:** Runs every 30 minutes (configurable)
- **Process:**
  1. Checks if enough tasks exist (min_tasks threshold)
  2. Checks cooldown period (avoid spam)
  3. Calls ReasoningAgent if conditions met
  4. Updates Dashboard.md with status
- **Output:** Triggers agent, logs activity

#### ReasoningAgent (`src/agents/reasoning_agent.py`)
- **Role:** Orchestrates skill pipeline
- **Dependencies:** Skill Registry (auto-discovers skills)
- **Process:**
  1. Initializes 3 core skills (TaskAnalyzer, ContextLoader, PlanGenerator)
  2. Calls skills sequentially
  3. Handles errors gracefully
- **Output:** Path to generated Plan.md

---

### 3. SKILLS SYSTEM (Modular AI Functions)

**Location:** `src/skills/`

#### Base Architecture
- **BaseSkill** (`base_skill.py`):
  - Abstract base class
  - Provides Groq API integration
  - Retry logic with exponential backoff
  - Audit logging support

#### Skill Categories:

**A. Analysis Skills (No AI Cost)**

**TaskAnalyzer** (`skills/analysis/task_analyzer.py`)
- **Input:** `max_tasks` parameter
- **Process:**
  1. Walks `Need_Action/` directory tree
  2. Reads `.md` files
  3. Parses YAML frontmatter (type, priority, status)
  4. Creates TaskItem objects
  5. Sorts by priority
- **Output:** List of TaskItem objects (max 20)

**ContextLoader** (`skills/analysis/context_loader.py`)
- **Input:** None
- **Process:**
  1. Reads `Company_Handbook.md`
  2. Reads `Business_Goals.md`
  3. Combines into single context string
- **Output:** String with business context (5000+ chars)

**B. Planning Skills (Uses Groq AI)**

**PlanGenerator** (`skills/planning/plan_generator.py`)
- **Input:** TaskItem[] + business context
- **Process:**
  1. Formats tasks into structured prompt
  2. Sends to Groq Llama 3.3 70B:
     - System: "You are an AI planning assistant"
     - User: Tasks + context + instructions
  3. Groq generates structured plan (JSON/Markdown)
  4. Parses response
  5. Saves to `Plans/Plan_{timestamp}_{title}.md`
  6. Logs reasoning to `Logs/reasoning_{timestamp}.md`
- **Output:** Plan object + file path
- **Cost:** $0 (FREE Groq tier)

**C. Content Skills (Uses Groq AI)**

**ContentOptimizer** (`skills/content/content_optimizer.py`)
- **Input:** Raw post text + platform (linkedin/instagram/x)
- **Process:**
  1. Sends to Groq with platform-specific guidelines
  2. Groq optimizes for engagement
  3. Returns improved content + hashtags + tips
- **Output:** Optimized post dict
- **Cost:** $0 (FREE Groq tier)

**D. Communication Skills (Uses Groq AI)**

**EmailClassifier** (`skills/communication/email_classifier.py`)
- **Input:** Email subject + body + sender
- **Process:**
  1. Sends to Groq for classification
  2. Groq analyzes urgency, type, entities
  3. Returns structured classification
- **Output:** Classification dict (urgency, type, priority 1-10)
- **Cost:** $0 (FREE Groq tier)

---

### 4. SKILL REGISTRY (Auto-Discovery)

**Location:** `src/skills/registry.py`

**Role:** Dependency injection container for skills

**Process:**
1. Scans `src/skills/` directory
2. Imports all Python files
3. Finds classes inheriting from BaseSkill
4. Registers by SKILL_NAME
5. Caches instances (singleton pattern)

**Usage:**
```python
registry = get_registry()
registry.auto_discover(Path("src/skills"))
skill = registry.get_skill("task_analyzer", vault_path="/path")
result = skill.execute(SkillInput(data={}))
```

---

### 5. VAULT STRUCTURE (Data Storage)

**Location:** `ai_employee_vault/`

```
ai_employee_vault/
├── Dashboard.md              ← Status overview
├── Company_Handbook.md       ← Business rules/policies
├── Business_Goals.md         ← Strategic objectives
│
├── Need_Action/              ← INBOX: Pending tasks
│   ├── email_replies/        ← Gmail watcher output
│   ├── business_tasks/       ← Manual/file watcher tasks
│   ├── social_posts/         ← Draft social content
│   └── whatsapp/             ← WhatsApp messages
│
├── Approved/                 ← READY: Human-approved content
│   ├── linkedin/             ← LinkedIn watcher input
│   ├── instagram/            ← Instagram watcher input
│   └── x/                    ← X watcher input
│
├── Plans/                    ← AI-generated action plans
│   └── Plan_{timestamp}_{title}.md
│
├── Logs/                     ← Audit & reasoning logs
│   ├── reasoning_{timestamp}.md
│   └── audit_{date}.jsonl
│
└── Done/                     ← ARCHIVE: Completed tasks
    ├── *.md                  ← Moved completed tasks
    └── assets/               ← Used images
```

---

## Complete Workflow Example

### Scenario: Important Email Arrives

**Step 1: INPUT (Gmail Watcher)**
```
Time: 09:00 AM
Gmail Watcher polls Gmail API
→ Finds unread important email from client
→ Creates: Need_Action/email_replies/EMAIL_19bb78834.md

Content:
---
type: email
from: client@company.com
subject: Urgent: Project deadline change
priority: high
status: pending
---

## Email Content
We need to move the project deadline to Friday...

## Suggested Actions
- [ ] Reply to sender
```

**Step 2: REASONING (Every 30 mins)**
```
Time: 09:30 AM
Reasoning Loop Orchestrator wakes up
→ Checks Need_Action/ folder
→ Finds 1 task (meets min_tasks threshold)
→ Triggers ReasoningAgent
```

**Step 3: AI PROCESSING (Skills Pipeline)**
```
ReasoningAgent.run_once():

1. TaskAnalyzer Skill:
   → Scans Need_Action/
   → Finds EMAIL_19bb78834.md
   → Parses YAML → TaskItem(type='email', priority='high')
   → Returns: [TaskItem]

2. ContextLoader Skill:
   → Reads Company_Handbook.md (2000 chars)
   → Reads Business_Goals.md (3500 chars)
   → Returns: "Company values: ... Goals: ..." (5500 chars)

3. PlanGenerator Skill:
   → Formats prompt:
     "You have 1 urgent email task from client...
      Business context: [5500 chars]
      Generate a plan..."

   → Calls Groq API (Llama 3.3 70B):
     Request: {model, messages, temperature=0.7}
     Response time: ~2 seconds (Groq is FAST!)
     Response: Structured plan with reasoning

   → Saves Plans/Plan_20260125_093045_Client_Email.md
   → Logs Logs/reasoning_20260125_093045.md
```

**Step 4: PLAN OUTPUT**
```
Plans/Plan_20260125_093045_Client_Email.md:

---
title: "Urgent Client Deadline Response"
created: 2026-01-25T09:30:45
complexity: low
status: pending
---

## Summary
Respond to client's urgent deadline change request

## Reasoning
High-priority email from established client regarding
project timeline. Requires immediate acknowledgment
within 2 hours per SLA in Company_Handbook.md

## Action Steps

### Step 1: Draft professional response
- Assignee: 🤝 hybrid (human drafts, AI reviews)
- Effort: low
- Related Tasks: EMAIL_19bb78834.md

Draft email acknowledging deadline change,
confirm new timeline feasibility, request
confirmation call.

### Step 2: Update project timeline
- Assignee: 👤 human
- Effort: medium
...
```

**Step 5: HUMAN APPROVAL**
```
Time: 09:35 AM
Human reads plan, approves approach
→ Drafts email response
→ (Future: Could use EmailResponder skill to draft)
→ Sends email manually
→ Moves EMAIL_19bb78834.md to Done/
```

**Step 6: SOCIAL MEDIA POST EXAMPLE**
```
Time: 10:00 AM
Human creates post about project success:

Approved/linkedin/project_milestone.md:
---
image_path: /path/to/image.jpg
---

Just completed a major project milestone! 🎉

Time: 10:01 AM
LinkedIn Watcher polls Approved/linkedin/
→ Finds project_milestone.md
→ Uses Playwright to:
  1. Login to LinkedIn (session cached)
  2. Click "Start a post"
  3. Upload image.jpg
  4. Insert text
  5. Click "Post"
→ Success!
→ Moves file to Done/
→ Moves image to Done/assets/
```

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|----------|
| AI Reasoning | Groq API (FREE) | Ultra-fast LLM inference |
| Model | Llama 3.3 70B | Planning & content generation |
| Browser Automation | Playwright | Social media posting |
| Email | Gmail API | Email monitoring |
| Data Storage | Markdown + YAML | Human-readable vault |
| Language | Python 3.12+ | Core implementation |
| Scheduling | Python loops | Watcher coordination |

---

## Execution Models

### Task Assignment Types (in Plans)

**🤖 Automated**
- Fully handled by watchers
- Example: Social media posting
- No human intervention needed

**🤝 Hybrid**
- Human + AI collaboration
- Example: Email drafting (human writes, AI optimizes)
- Human has final approval

**👤 Human**
- Requires manual action
- Example: Phone calls, meetings
- AI only provides guidance

---

## Error Handling & Recovery (Gold Tier)

**Retry Handler** (`src/core/retry_handler.py`)
- Exponential backoff (1s, 2s, 4s...)
- Max 3 attempts
- Handles: NetworkTimeout, RateLimitExceeded, ServiceUnavailable

**Audit Logger** (`src/logging/audit_logger.py`)
- Logs all skill executions
- Records success/failure with timestamps
- JSON Lines format for easy parsing

**Health Monitor** (`src/core/health_monitor.py`)
- Checks service health
- Alerts on failures

---

## Cost Breakdown

| Service | Usage | Cost |
|---------|-------|------|
| Groq API | All AI reasoning | **$0** (Free tier) |
| Gmail API | Email monitoring | $0 (Free quota) |
| Playwright | Automation | $0 (Open source) |
| Compute | Local Python | $0 (Run on your machine) |
| **TOTAL** | | **$0/month** |

---

## Development Commands

### Start Watchers
```bash
# Input collectors
python -m src.watchers.gmail_watcher
python -m src.watchers.whatsapp_watcher

# Output executors
python -m src.watchers.linkedin_watcher
python -m src.watchers.insta_watcher
python -m src.watchers.x_watcher
```

### Start Reasoning Loop
```bash
# Run once
python -m src.orchestrator.reasoning_loop --once

# Run continuously (every 30 mins)
python -m src.orchestrator.reasoning_loop --interval 1800

# Use different model
python -m src.orchestrator.reasoning_loop \
  --model llama-3.1-8b-instant \
  --verbose
```

### Test Skills
```bash
# Test all skills
pytest tests/skills/

# Test specific skill
pytest tests/skills/test_task_analyzer.py -v

# With coverage
pytest --cov=src/skills tests/skills/
```

---

## File Lifecycle

```
1. CREATION (Watcher)
   → Task created in Need_Action/

2. COLLECTION (TaskAnalyzer)
   → Scanned and parsed

3. REASONING (PlanGenerator)
   → Included in AI plan

4. APPROVAL (Human)
   → Moved to Approved/ OR Done/

5. EXECUTION (Watcher)
   → Posted/sent/completed

6. ARCHIVAL (Watcher)
   → Moved to Done/
```

---

## Summary

**This is a modular, skill-based AI employee that:**

1. **Monitors** multiple channels via Watchers
2. **Collects** tasks into a centralized vault
3. **Reasons** about tasks using FREE Groq AI
4. **Plans** actions with human-readable markdown
5. **Executes** approved tasks automatically
6. **Archives** completed work

**All for $0/month using the FREE Groq API!**

**Architecture Benefits:**
- ✅ Modular skills (easy to extend)
- ✅ Human-in-the-loop (safe & controlled)
- ✅ Markdown-based (readable by humans & AI)
- ✅ Zero cost (free tier services)
- ✅ Silver Tier compliant (skill-based AI)

---

## Next Steps (Gold Tier)

- [ ] Odoo accounting integration (MCP server)
- [ ] Ralph Wiggum autonomous loop
- [ ] Advanced error recovery
- [ ] Multi-step task execution
- [ ] Weekly CEO briefing generation
