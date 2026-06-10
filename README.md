# FTE_Employee - AI Employee Automation System

**Silver Tier Compliant** - Modular skill-based AI agent using FREE Groq API

---

## Overview

FTE_Employee is an automated AI employee system that monitors multiple communication channels (Gmail, LinkedIn, Instagram, X/Twitter, WhatsApp), analyzes pending tasks, and generates actionable plans using AI reasoning.

**Key Features:**
- 🤖 **Modular Skills System** - Silver Tier compliant architecture
- 💰 **$0/month Cost** - Uses FREE Groq API (Llama 3.3 70B)
- 📧 **Multi-Channel Monitoring** - Gmail, LinkedIn, Instagram, X, WhatsApp
- 📋 **Intelligent Planning** - AI-generated action plans with reasoning
- 🔄 **Automated Workflows** - Continuous monitoring and task processing
- 🧪 **Fully Tested** - Comprehensive test suite with pytest

---

## Architecture

### Silver Tier Compliance

This project has been refactored from monolithic code into **modular Python skills** for Silver Tier compliance. All AI functionality is implemented as discrete, reusable skill classes.

```
hackathon_zero/
├── src/
│   ├── skills/                    # Modular skill system (Silver Tier)
│   │   ├── base_skill.py         # Base class with Groq integration
│   │   ├── registry.py           # Skill discovery and registration
│   │   ├── analysis/             # Analysis skills (no LLM)
│   │   │   ├── task_analyzer.py
│   │   │   └── context_loader.py
│   │   ├── planning/             # Planning skills (uses Groq)
│   │   │   └── plan_generator.py
│   │   ├── content/              # Content skills (uses Groq)
│   │   │   └── content_optimizer.py
│   │   └── communication/        # Communication skills (uses Groq)
│   │       └── email_classifier.py
│   │
│   ├── agents/
│   │   └── reasoning_agent.py    # Orchestrates skills
│   │
│   ├── watchers/                 # Channel monitors
│   │   ├── gmail_watcher.py      # Gmail monitoring
│   │   ├── linkedin_watcher.py   # LinkedIn posting
│   │   ├── insta_watcher.py      # Instagram posting
│   │   ├── x_watcher.py          # X/Twitter posting
│   │   └── whatsapp_watcher.py   # WhatsApp monitoring
│   │
│   └── orchestrator/
│       └── reasoning_loop.py     # Main orchestration loop
│
├── tests/
│   └── skills/                   # Skill tests
│
├── ai_employee_vault/            # Data storage
│   ├── Need_Action/              # Pending tasks
│   ├── Approved/                 # Approved content
│   ├── Plans/                    # Generated plans
│   ├── Done/                     # Completed items
│   └── Logs/                     # Reasoning logs
│
├── SKILLS.md                     # Detailed skill documentation
└── README.md                     # This file
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Free Groq API key: https://console.groq.com/keys
- Playwright (for watchers)

### Installation

```bash
# Clone the repository
cd hackathon_zero

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Configuration

1. Create `.env` file:
```bash
GROQ_API_KEY=your_groq_api_key_here
VAULT_PATH=/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault
```

2. Set up vault structure:
```bash
mkdir -p ai_employee_vault/{Need_Action/{email_replies,business_tasks,social_posts,whatsapp},Approved/{linkedin,instagram,x},Plans,Done,Logs}
```

### Running the System

#### 1. Start Reasoning Agent (Main Loop)

```bash
# Run once
python -m src.orchestrator.reasoning_loop --once

# Run continuously (checks every 30 minutes)
python -m src.orchestrator.reasoning_loop --interval 1800
```

#### 2. Start Watchers

```bash
# Gmail watcher
python -m src.watchers.gmail_watcher

# LinkedIn poster
python -m src.watchers.linkedin_watcher

# Instagram poster
python -m src.watchers.insta_watcher

# X/Twitter poster
python -m src.watchers.x_watcher

# WhatsApp monitor
python -m src.watchers.whatsapp_watcher
```

---

## Skills System

The project uses a **modular skill system** for Silver Tier compliance. See [SKILLS.md](SKILLS.md) for complete documentation.

### Available Skills

| Skill | Category | Uses AI | Description |
|-------|----------|---------|-------------|
| **TaskAnalyzer** | Analysis | ❌ No | Collect and parse tasks from Need_Action |
| **ContextLoader** | Analysis | ❌ No | Load business goals and handbook |
| **PlanGenerator** | Planning | ✅ Groq | Generate action plans with AI reasoning |
| **ContentOptimizer** | Content | ✅ Groq | Optimize social media posts |
| **EmailClassifier** | Communication | ✅ Groq | Classify and analyze emails |

### Using Skills

```python
from skills import get_registry, SkillInput

# Get global registry
registry = get_registry()

# Auto-discover all skills
from pathlib import Path
registry.auto_discover(Path("src/skills"))

# Use a skill
task_analyzer = registry.get_skill("task_analyzer", vault_path="/path/to/vault")
result = task_analyzer.execute(SkillInput(data={"max_tasks": 20}))

tasks = result.result  # List of TaskItem objects
```

---

## Workflow

### 1. Task Collection

Watchers monitor channels and create task files in `Need_Action/`:

```
Need_Action/
├── email_replies/
│   └── urgent_client_email.md
├── business_tasks/
│   └── invoice_reminder.md
├── social_posts/
│   └── linkedin_post.md
└── whatsapp/
    └── msg_1234567890.txt
```

### 2. AI Reasoning

Every 30 minutes, the reasoning loop:

1. **TaskAnalyzer** collects pending tasks
2. **ContextLoader** loads business context
3. **PlanGenerator** uses Groq to create Plan.md

Example Plan.md:
```markdown
---
title: "Client Communication and Invoice Management"
created: 2026-01-18T14:30:22
complexity: moderate
status: pending
model: llama-3.3-70b-versatile
---

# Client Communication and Invoice Management

## Summary
Address urgent client email regarding project timeline and send
outstanding invoice reminder to ensure payment within deadline.

## Reasoning
The urgent client email requires immediate attention due to project
deadline implications...

## Action Steps

### Step 1: Reply to urgent client email
- **Assignee:** 🤝 hybrid
- **Effort:** medium
- **Related Tasks:** urgent_client_email.md

Draft professional response addressing timeline concerns...

### Step 2: Send invoice reminder
- **Assignee:** 🤖 automated
- **Effort:** low
- **Related Tasks:** invoice_reminder.md

Use automated email template for outstanding invoice...

## Risks
- ⚠️ Client may push back on timeline
- ⚠️ Invoice payment may be delayed

## Success Criteria
- ✅ Client email replied within 2 hours
- ✅ Invoice reminder sent
- ✅ Updated project timeline documented
```

### 3. Action Execution

Approved content in `Approved/` is automatically posted by watchers:

```
Approved/
├── linkedin/
│   └── post_about_project.md
├── instagram/
│   └── behind_the_scenes.md
└── x/
    └── quick_tip.md
```

Watchers post content and move files to `Done/`.

---

## Testing

```bash
# Run all tests
pytest

# Run skill tests specifically
pytest tests/skills/ -v

# Run with coverage
pytest --cov=src/skills tests/skills/

# Run specific test
pytest tests/skills/test_task_analyzer.py::test_task_analyzer_with_tasks
```

---

## Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| AI Reasoning (5 skills) | Groq API | **$0** (Free tier) |
| Task Analysis | Local Python | $0 |
| Watchers (5 channels) | Playwright | $0 |
| **Total** | | **$0/month** |

---

## Configuration Options

### Reasoning Agent

```bash
python -m src.orchestrator.reasoning_loop \
  --vault /path/to/vault \
  --interval 1800 \           # Check interval (seconds)
  --min-tasks 1 \             # Minimum tasks before running
  --cooldown 60 \             # Cooldown after plan (minutes)
  --model llama-3.3-70b-versatile \
  --verbose
```

### Watchers

Each watcher supports:
- Custom vault paths
- Check intervals
- Session persistence
- Error logging

---

## Development

### Adding a New Skill

1. Create skill file in appropriate category:

```python
# src/skills/analysis/my_skill.py
from ..base_skill import BaseSkill, SkillInput, SkillOutput

class MySkill(BaseSkill):
    SKILL_NAME = "my_skill"
    REQUIRES_LLM = False  # or True for Groq
    DESCRIPTION = "What this skill does"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        # Implementation
        return SkillOutput(result="data", success=True)
```

2. Add tests:

```python
# tests/skills/test_my_skill.py
def test_my_skill():
    skill = MySkill(vault_path="/tmp/test")
    result = skill.execute(SkillInput(data={}))
    assert result.success == True
```

3. Skill is auto-discovered by registry!

### Project Structure

- `src/skills/` - Modular skill classes
- `src/agents/` - Agent orchestration
- `src/watchers/` - Channel monitors
- `src/orchestrator/` - Main loop
- `tests/` - Test suite
- `ai_employee_vault/` - Data storage

---

## Troubleshooting

### Groq API Key Not Found

```
ValueError: GROQ_API_KEY not found
```

**Solution:** Add to `.env`:
```bash
GROQ_API_KEY=your_key_here
```

Get free key: https://console.groq.com/keys

### Skill Not Found

```
KeyError: Skill 'task_analyzer' not found
```

**Solution:** Ensure auto-discovery ran:
```python
registry.auto_discover(Path("src/skills"))
```

### Playwright Browser Not Installed

```
Error: Executable doesn't exist at /path/to/chromium
```

**Solution:**
```bash
playwright install chromium
```

---

## Monitoring

### Check Logs

```bash
# Reasoning logs
cat ai_employee_vault/Logs/reasoning_*.md

# Watcher logs (console output)
```

### View Generated Plans

```bash
ls -la ai_employee_vault/Plans/
```

### Check Task Queue

```bash
find ai_employee_vault/Need_Action -name "*.md" -type f
```

---

## Silver Tier Compliance

✅ **All AI functionality implemented as Agent Skills**

- **Modular:** Each skill is a separate Python class
- **Discoverable:** Auto-discovered via SkillRegistry
- **Reusable:** Skills can be used independently
- **Testable:** Unit tests for each skill
- **Extensible:** Easy to add new skills
- **Cost-effective:** $0/month using FREE Groq API

**Before:** 456-line monolithic reasoning_agent.py
**After:** 5 modular skills + 143-line orchestrator

---

## Features

### Current Features

- ✅ Multi-channel monitoring (Gmail, LinkedIn, Instagram, X, WhatsApp)
- ✅ AI-powered plan generation
- ✅ Automated content posting
- ✅ Email classification and triage
- ✅ Content optimization for social media
- ✅ Modular skill system
- ✅ Comprehensive testing
- ✅ $0/month cost

### Roadmap

- 🔲 Web dashboard for monitoring
- 🔲 More intelligence skills (sentiment analysis, meeting scheduling)
- 🔲 Slack integration
- 🔲 Calendar integration
- 🔲 Advanced analytics

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your skill or feature
4. Write tests
5. Submit a pull request

See [SKILLS.md](SKILLS.md) for skill development guidelines.

---

## License

MIT License - See LICENSE file

---

## Support

- 📖 Documentation: [SKILLS.md](SKILLS.md)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

## Acknowledgments

- **Groq** - FREE ultra-fast inference API
- **Playwright** - Browser automation
- **Python Community** - Amazing libraries

---

**Built for Silver Tier compliance with $0/month cost using FREE Groq API.**
