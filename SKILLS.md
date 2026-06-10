# Agent Skills Documentation

## Overview

This document describes the modular skill system implemented for **Silver Tier compliance**. The FTE_Employee project has been refactored to use discrete, reusable Python skill classes instead of monolithic code.

All skills use the **FREE Groq API** for AI reasoning, maintaining **$0/month cost**.

---

## Architecture

### Core Components

1. **BaseSkill** (`src/skills/base_skill.py`)
   - Abstract base class for all skills
   - Provides Groq API integration
   - Defines standard execute() interface

2. **SkillRegistry** (`src/skills/registry.py`)
   - Auto-discovers skills from `src/skills/` directory
   - Manages skill registration and instantiation
   - Caches skill instances for performance

3. **Skill Categories**
   - **Analysis Skills** - Data parsing and collection (no LLM)
   - **Planning Skills** - Plan generation using Groq
   - **Content Skills** - Content optimization using Groq
   - **Communication Skills** - Email and message handling using Groq

---

## Available Skills

### Analysis Skills (No Groq Cost)

#### 1. TaskAnalyzer
- **File:** `src/skills/analysis/task_analyzer.py`
- **Skill Name:** `task_analyzer`
- **Requires LLM:** No
- **Description:** Collect and parse tasks from Need_Action folder

**Purpose:**
Scans markdown files in `Need_Action/` and subfolders, parses YAML frontmatter, and returns structured TaskItem objects sorted by priority.

**Input:**
```python
SkillInput(data={
    "max_tasks": 20  # Maximum tasks to collect
})
```

**Output:**
```python
SkillOutput(
    result=[TaskItem, TaskItem, ...],  # List of TaskItem objects
    success=True,
    metadata={"task_count": 15}
)
```

**Example:**
```python
from skills import get_registry, SkillInput

registry = get_registry()
analyzer = registry.get_skill("task_analyzer", vault_path="/path/to/vault")

input_data = SkillInput(data={"max_tasks": 20})
result = analyzer.execute(input_data)

tasks = result.result  # List of TaskItem objects
```

---

#### 2. ContextLoader
- **File:** `src/skills/analysis/context_loader.py`
- **Skill Name:** `context_loader`
- **Requires LLM:** No
- **Description:** Load business goals and company handbook

**Purpose:**
Reads `Business_Goals.md` and `Company_Handbook.md` from the vault and returns combined context string for use in plan generation.

**Input:**
```python
SkillInput(data={})  # No input required
```

**Output:**
```python
SkillOutput(
    result="## Business Goals\n...\n## Company Handbook\n...",
    success=True,
    metadata={"context_length": 5420}
)
```

**Example:**
```python
loader = registry.get_skill("context_loader", vault_path="/path/to/vault")
result = loader.execute(SkillInput(data={}))
context = result.result
```

---

### Planning Skills (Uses Groq)

#### 3. PlanGenerator
- **File:** `src/skills/planning/plan_generator.py`
- **Skill Name:** `plan_generator`
- **Requires LLM:** Yes (Groq)
- **Description:** Generate action plans from tasks using Groq LLM

**Purpose:**
Takes a list of tasks and business context, uses Groq LLM to reason about them, and generates a detailed `Plan.md` file in the `Plans/` directory.

**Input:**
```python
SkillInput(
    data={
        "tasks": [TaskItem, TaskItem, ...]  # List from TaskAnalyzer
    },
    context={
        "business_context": "..."  # String from ContextLoader
    }
)
```

**Output:**
```python
SkillOutput(
    result=Plan(...),  # Plan object
    success=True,
    metadata={
        "plan_path": "/path/to/Plans/Plan_20260118_143022_Task_Management.md",
        "task_count": 5,
        "step_count": 8
    }
)
```

**Example:**
```python
generator = registry.get_skill(
    "plan_generator",
    vault_path="/path/to/vault",
    groq_model="llama-3.3-70b-versatile"
)

plan_input = SkillInput(
    data={"tasks": tasks},
    context={"business_context": context}
)
result = generator.execute(plan_input)

plan_path = result.metadata["plan_path"]  # Path to saved plan
```

**Features:**
- Chain-of-thought reasoning
- Logs thinking process to `Logs/`
- Generates markdown plan with:
  - Executive summary
  - Detailed reasoning
  - Step-by-step actions
  - Risk assessment
  - Success criteria

---

### Content Skills (Uses Groq)

#### 4. ContentOptimizer
- **File:** `src/skills/content/content_optimizer.py`
- **Skill Name:** `content_optimizer`
- **Requires LLM:** Yes (Groq)
- **Description:** Optimize social media content for engagement using Groq

**Purpose:**
Uses Groq to analyze and improve social media posts for maximum engagement. Tailors suggestions to platform-specific best practices (LinkedIn, Instagram, X/Twitter).

**Input:**
```python
SkillInput(data={
    "content": "Original post text here",
    "platform": "linkedin",  # or "instagram", "x", "twitter"
    "tone": "professional"  # Optional, default: "professional"
})
```

**Output:**
```python
SkillOutput(
    result={
        "optimized_content": "Improved post text...",
        "suggested_hashtags": ["#Marketing", "#Business"],
        "improvements_made": ["Added call-to-action", "Improved clarity"],
        "engagement_tips": ["Post during peak hours", "Add visual"]
    },
    success=True,
    metadata={
        "platform": "linkedin",
        "original_length": 120,
        "optimized_length": 145
    }
)
```

**Example:**
```python
optimizer = registry.get_skill(
    "content_optimizer",
    vault_path="/path/to/vault"
)

input_data = SkillInput(data={
    "content": "Just finished a great project!",
    "platform": "linkedin",
    "tone": "professional"
})

result = optimizer.execute(input_data)
optimized = result.result["optimized_content"]
```

**Supported Platforms:**
- **LinkedIn:** Professional, value-focused, 3-5 hashtags
- **Instagram:** Visual storytelling, 10-15 hashtags, emoji-friendly
- **X/Twitter:** Concise, 280 chars, 1-3 hashtags

---

### Communication Skills (Uses Groq)

#### 5. EmailClassifier
- **File:** `src/skills/communication/email_classifier.py`
- **Skill Name:** `email_classifier`
- **Requires LLM:** Yes (Groq)
- **Description:** Classify and analyze emails using Groq LLM

**Purpose:**
Classifies emails by urgency and type, extracts key entities (clients, deadlines, amounts), and suggests appropriate actions for inbox triage.

**Input:**
```python
SkillInput(data={
    "subject": "Urgent: Project deadline moved up",
    "body": "Hi, we need to move the deadline to Friday...",
    "sender": "client@example.com"  # Optional
})
```

**Output:**
```python
SkillOutput(
    result={
        "urgency": "urgent",  # urgent|high|normal|low|spam
        "email_type": "inquiry",  # inquiry|invoice|support|meeting|update|newsletter|personal
        "confidence": "high",
        "key_entities": {
            "client_names": ["ABC Corp"],
            "deadlines": ["Friday"],
            "amounts": [],
            "action_items": ["Reschedule project timeline"]
        },
        "suggested_actions": ["Reply within 1 hour", "Update project plan"],
        "reasoning": "Email mentions urgent deadline change from known client",
        "priority_score": 9
    },
    success=True
)
```

**Example:**
```python
classifier = registry.get_skill(
    "email_classifier",
    vault_path="/path/to/vault"
)

input_data = SkillInput(data={
    "subject": "Invoice #1234",
    "body": "Please find attached invoice for $5000...",
    "sender": "accounting@client.com"
})

result = classifier.execute(input_data)

if classifier.should_create_action(result.result):
    # Create action file in Need_Action/email_replies/
    pass
```

**Classification Categories:**
- **Urgency:** urgent, high, normal, low, spam
- **Type:** inquiry, invoice, support, meeting, update, newsletter, personal
- **Priority Score:** 1-10 numerical priority

---

## Using Skills in Your Code

### Method 1: Via ReasoningAgent

The `ReasoningAgent` automatically uses skills:

```python
from src.agents.reasoning_agent import ReasoningAgent

agent = ReasoningAgent(
    vault_path="/path/to/vault",
    model="llama-3.3-70b-versatile"
)

# Runs complete pipeline: TaskAnalyzer → ContextLoader → PlanGenerator
plan_path = agent.run_once(max_tasks=20)
```

### Method 2: Direct Skill Usage

Use skills directly for more control:

```python
from skills import get_registry, SkillInput

# Get global registry
registry = get_registry()

# Auto-discover all skills
from pathlib import Path
skills_path = Path("src/skills")
registry.auto_discover(skills_path)

# Use individual skills
task_analyzer = registry.get_skill("task_analyzer", vault_path="/path/to/vault")
context_loader = registry.get_skill("context_loader", vault_path="/path/to/vault")
plan_generator = registry.get_skill(
    "plan_generator",
    vault_path="/path/to/vault",
    groq_model="llama-3.3-70b-versatile"
)

# Execute skills in sequence
tasks_result = task_analyzer.execute(SkillInput(data={"max_tasks": 20}))
context_result = context_loader.execute(SkillInput(data={}))

plan_result = plan_generator.execute(SkillInput(
    data={"tasks": tasks_result.result},
    context={"business_context": context_result.result}
))
```

### Method 3: Creating Custom Skills

Create your own skills by inheriting from `BaseSkill`:

```python
from skills.base_skill import BaseSkill, SkillInput, SkillOutput

class MyCustomSkill(BaseSkill):
    SKILL_NAME = "my_custom_skill"
    REQUIRES_LLM = True  # Set to False if no Groq needed
    DESCRIPTION = "My custom skill description"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        try:
            # Your skill logic here
            if self.REQUIRES_LLM:
                response = self._call_groq(
                    system_prompt="You are a helpful assistant",
                    user_prompt="Analyze this data..."
                )

            return SkillOutput(
                result={"data": "processed"},
                success=True
            )
        except Exception as e:
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

# Register and use
from skills import get_registry

registry = get_registry()
registry.register(MyCustomSkill)

skill = registry.get_skill("my_custom_skill", vault_path="/path")
result = skill.execute(SkillInput(data={}))
```

---

## Testing Skills

Run skill tests with pytest:

```bash
# Run all skill tests
pytest tests/skills/

# Run specific test file
pytest tests/skills/test_task_analyzer.py

# Run with verbose output
pytest tests/skills/ -v

# Run with coverage
pytest tests/skills/ --cov=src/skills
```

---

## Cost Analysis

| Skill | Uses Groq | Cost |
|-------|-----------|------|
| TaskAnalyzer | ❌ No | $0 |
| ContextLoader | ❌ No | $0 |
| PlanGenerator | ✅ Yes | $0 (Free tier) |
| ContentOptimizer | ✅ Yes | $0 (Free tier) |
| EmailClassifier | ✅ Yes | $0 (Free tier) |

**Total Cost:** $0/month (all use FREE Groq API)

---

## Silver Tier Compliance

✅ **Requirement Met:** "All AI functionality should be implemented as Agent Skills"

**How We Comply:**
1. **Modular Skills:** Each skill is a separate Python class
2. **Discoverable:** Skills are auto-discovered via `SkillRegistry`
3. **Reusable:** Skills can be used independently or composed
4. **Testable:** Each skill has unit tests
5. **Extensible:** Easy to add new skills without modifying existing code

**Skills vs. Monolithic Code:**

**Before (Monolithic):**
```python
class ReasoningAgent:
    def _parse_markdown_file(self, ...):  # 25 lines
    def collect_tasks(self, ...):  # 24 lines
    def _load_business_context(self, ...):  # 15 lines
    def reason_and_plan(self, ...):  # 82 lines
    def _generate_plan_markdown(self, ...):  # 49 lines
    # Total: 456 lines in one file
```

**After (Modular Skills):**
```python
# src/skills/analysis/task_analyzer.py (135 lines)
# src/skills/analysis/context_loader.py (74 lines)
# src/skills/planning/plan_generator.py (378 lines)
# src/skills/content/content_optimizer.py (197 lines)
# src/skills/communication/email_classifier.py (223 lines)

# ReasoningAgent (143 lines) - Just orchestrates skills
```

**Benefits:**
- ✅ Each skill can be tested independently
- ✅ Skills are reusable across different agents
- ✅ Easy to add new skills without touching existing code
- ✅ Clear separation of concerns
- ✅ Silver Tier compliant

---

## Troubleshooting

### Skill Not Found Error

```
KeyError: Skill 'my_skill' not found
```

**Solution:** Ensure auto-discovery has run:
```python
from pathlib import Path
registry.auto_discover(Path("src/skills"))
```

### Groq API Key Missing

```
ValueError: Skill plan_generator requires LLM but GROQ_API_KEY not found
```

**Solution:** Set your Groq API key in `.env`:
```bash
GROQ_API_KEY=your_key_here
```

Get a free key at: https://console.groq.com/keys

### Import Error

```
ModuleNotFoundError: No module named 'skills'
```

**Solution:** Ensure `src/` is in Python path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## Future Skills

Potential skills to implement:

1. **PriorityScorer** - Assign priority scores using Groq
2. **DependencyMapper** - Identify task dependencies using Groq
3. **RiskAssessor** - Assess risks in plans using Groq
4. **CaptionGenerator** - Generate image captions using Groq
5. **HashtagSuggester** - Suggest hashtags using Groq
6. **EmailResponder** - Generate email draft responses using Groq
7. **SentimentAnalyzer** - Analyze sentiment in communications using Groq
8. **MeetingScheduler** - Parse and schedule meeting times using Groq

---

## Contributing

To add a new skill:

1. Create a new file in the appropriate category folder:
   - `src/skills/analysis/` - Data collection and parsing
   - `src/skills/planning/` - Planning and strategy
   - `src/skills/content/` - Content generation and optimization
   - `src/skills/communication/` - Communication handling

2. Inherit from `BaseSkill`:
   ```python
   from ..base_skill import BaseSkill, SkillInput, SkillOutput

   class MySkill(BaseSkill):
       SKILL_NAME = "my_skill"
       REQUIRES_LLM = True  # or False
       DESCRIPTION = "What this skill does"

       def execute(self, input_data: SkillInput) -> SkillOutput:
           # Implementation
           pass
   ```

3. Add tests in `tests/skills/test_my_skill.py`

4. Update this documentation

5. The skill will be auto-discovered by `SkillRegistry`

---

## Summary

The FTE_Employee project now uses a **modular skill system** for Silver Tier compliance:

- ✅ **5 Core Skills** implemented and tested
- ✅ **Auto-discovery** via SkillRegistry
- ✅ **$0/month cost** (all use FREE Groq API)
- ✅ **Fully tested** with pytest
- ✅ **Documented** with examples
- ✅ **Extensible** for future skills

**No cost increase, full Silver Tier compliance, maximum modularity.**
