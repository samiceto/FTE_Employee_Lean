# FTE_Employee - Quick Reference Guide

## What This Project Does
An AI assistant that monitors emails/social media, thinks about what to do, creates plans, and automatically posts content. All using FREE AI (Groq API).

---

## Simple Data Flow

```
INPUTS → STORAGE → AI THINKS → HUMAN APPROVES → OUTPUTS
```

### 1. INPUTS (Watchers Collect Data)
- **Gmail Watcher** → saves emails to `Need_Action/email_replies/`
- **WhatsApp Watcher** → saves messages to `Need_Action/whatsapp/`
- **File Watcher** → monitors folders for new files

### 2. STORAGE (Vault = Your Files)
```
ai_employee_vault/
├── Need_Action/     ← Pending tasks go here
├── Approved/        ← Content ready to post
├── Plans/           ← AI-generated plans
├── Done/            ← Completed tasks
└── Logs/            ← Activity logs
```

### 3. AI THINKS (Every 30 Minutes)
**Reasoning Loop** wakes up and:
1. Checks `Need_Action/` for tasks
2. Reads your `Company_Handbook.md` for context
3. Sends everything to Groq AI (FREE)
4. AI thinks and creates a `Plan.md` file
5. Saves plan to `Plans/` folder

**Example Plan.md:**
```markdown
## Summary
You have 5 urgent emails and 2 social media posts

## Reasoning
Emails need replies within 2 hours per company policy.
Posts should go out during peak engagement times.

## Action Steps
### Step 1: Reply to client email
- Priority: HIGH
- Do this first!

### Step 2: Post to LinkedIn
- Wait until 2pm for better engagement
```

### 4. HUMAN APPROVES
- You read the plan
- Create approved content in `Approved/linkedin/post.md`
- Or handle tasks manually

### 5. OUTPUTS (Watchers Post Content)
- **LinkedIn Watcher** → checks `Approved/linkedin/` every minute
  - Finds `post.md`
  - Logs into LinkedIn (automated browser)
  - Posts content + image
  - Moves file to `Done/`

- Same for Instagram, Twitter, etc.

---

## The 3 Core Skills (What AI Does)

### 1. TaskAnalyzer (No AI, just reads files)
- Scans `Need_Action/` folder
- Reads all `.md` files
- Makes a list of tasks
- Sorts by priority

### 2. ContextLoader (No AI, just reads files)
- Reads `Company_Handbook.md`
- Reads `Business_Goals.md`
- Gives AI context about your business

### 3. PlanGenerator (Uses Groq AI - FREE)
- Takes: Task list + business context
- Sends to: Groq Llama 3.3 70B model
- Gets back: Smart plan with reasoning
- Saves to: `Plans/` folder

---

## File Journey Example

### Email Arrives
```
09:00 AM - Email from client arrives
         ↓
09:02 AM - Gmail Watcher checks inbox
         → Creates: Need_Action/email_replies/EMAIL_123.md
         ↓
09:30 AM - Reasoning Loop wakes up
         → TaskAnalyzer finds 1 task
         → ContextLoader loads business rules
         → PlanGenerator asks Groq AI what to do
         → Groq thinks (2 seconds)
         → Creates: Plans/Plan_Client_Email.md
         ↓
09:35 AM - YOU read the plan
         → Draft email reply
         → Send email
         → Move EMAIL_123.md to Done/
```

### Social Post Flow
```
10:00 AM - YOU create: Approved/linkedin/announcement.md
         ↓
10:01 AM - LinkedIn Watcher sees new file
         → Opens browser (automated)
         → Logs into LinkedIn
         → Clicks "Start a post"
         → Types your text
         → Uploads image
         → Clicks "Post"
         → Success!
         → Moves file to Done/
```

---

## Key Files & What They Do

| File Path | What It Does | When It Runs |
|-----------|-------------|--------------|
| `src/watchers/gmail_watcher.py` | Monitors Gmail, creates tasks | Every 2 minutes |
| `src/watchers/linkedin_watcher.py` | Posts to LinkedIn | Every 60 seconds |
| `src/orchestrator/reasoning_loop.py` | Triggers AI to make plans | Every 30 minutes |
| `src/agents/reasoning_agent.py` | Coordinates the 3 skills | When triggered |
| `src/skills/planning/plan_generator.py` | Calls Groq AI to think | When agent runs |

---

## How to Run Everything

### Option 1: Run Watchers Separately (Recommended)
```bash
# Terminal 1: Monitor emails
python -m src.watchers.gmail_watcher

# Terminal 2: Monitor WhatsApp
python -m src.watchers.whatsapp_watcher

# Terminal 3: Post to LinkedIn
python -m src.watchers.linkedin_watcher

# Terminal 4: AI Reasoning (every 30 mins)
python -m src.orchestrator.reasoning_loop --interval 1800
```

### Option 2: Run Once for Testing
```bash
# Just generate one plan and exit
python -m src.orchestrator.reasoning_loop --once
```

---

## Folder Structure Cheat Sheet

```
Need_Action/
├── email_replies/     ← Emails that need replies
├── business_tasks/    ← Manual tasks
├── social_posts/      ← Draft posts
└── whatsapp/          ← Messages

Approved/
├── linkedin/          ← Ready to post to LinkedIn
├── instagram/         ← Ready to post to Instagram
└── x/                 ← Ready to post to Twitter

Plans/                 ← AI-generated plans
Done/                  ← Completed tasks
Logs/                  ← Activity logs
```

---

## Common Scenarios

### Scenario: Email Needs Reply
1. Gmail Watcher creates file in `Need_Action/email_replies/`
2. Reasoning Loop generates plan
3. You read plan and reply to email
4. Move file to `Done/`

### Scenario: Post to Social Media
1. You create file in `Approved/linkedin/`
2. LinkedIn Watcher sees it
3. Watcher posts automatically
4. Watcher moves file to `Done/`

### Scenario: Check What's Pending
1. Look in `Need_Action/` folder
2. Count `.md` files
3. Read latest plan in `Plans/` folder

---

## Cost: $0/month

| What | Cost |
|------|------|
| Groq AI (thinking) | FREE |
| Gmail API (emails) | FREE |
| Playwright (automation) | FREE |
| Python (running) | FREE |
| **TOTAL** | **$0** |

---

## Configuration (.env file)

```bash
# Required
GROQ_API_KEY=your_free_key_from_groq_console
VAULT_PATH=/path/to/ai_employee_vault

# For LinkedIn posting
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password

# For Gmail monitoring
# (Need token.json from OAuth flow)
```

---

## Troubleshooting

### No plans being generated?
- Check `Need_Action/` has tasks (`.md` files)
- Check reasoning loop is running
- Look at logs for errors

### LinkedIn not posting?
- Check `Approved/linkedin/` has `.md` files
- Check LinkedIn watcher is running
- Verify login credentials in `.env`

### Groq API errors?
- Check GROQ_API_KEY in `.env`
- Get free key at: https://console.groq.com/keys
- Check internet connection

---

## Quick Commands

```bash
# See if tasks exist
ls ai_employee_vault/Need_Action/**/*.md

# See latest plan
ls -t ai_employee_vault/Plans/*.md | head -1

# Count pending tasks
find ai_employee_vault/Need_Action -name "*.md" | wc -l

# Run reasoning once
python -m src.orchestrator.reasoning_loop --once

# Start all watchers (in separate terminals)
python -m src.watchers.gmail_watcher
python -m src.watchers.linkedin_watcher
python -m src.orchestrator.reasoning_loop --interval 1800
```

---

## Summary in 3 Sentences

1. **Watchers** collect emails/messages and save as markdown files in `Need_Action/`
2. **AI Reasoning** (every 30 mins) reads tasks, asks Groq AI to think, saves plans to `Plans/`
3. **Watchers** automatically post content from `Approved/` to social media and move to `Done/`

**It's like having a smart assistant that monitors everything, thinks about it, and handles the routine stuff!**
