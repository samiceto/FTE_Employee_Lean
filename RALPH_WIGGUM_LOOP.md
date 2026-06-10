# Ralph Wiggum Loop - Autonomous Execution System

🤖 **"I'm helping!"** - Ralph Wiggum

The Ralph Wiggum Loop is an autonomous execution system that executes Plan.md files created by the Reasoning Loop. Named after Ralph Wiggum from The Simpsons - it's autonomous, persistent, and always helping!

## 🏗️ Architecture

The Ralph Wiggum Loop follows the same architecture pattern as the Reasoning Loop for consistency:

```
ExecutionAgent (Groq-powered, FREE)
├─ TaskDecomposer skill (Groq LLM)
├─ TaskSelector skill (no LLM)
├─ TaskExecutor skill (no LLM)
├─ ProgressEvaluator skill (Groq LLM)
└─ PlanAdjuster skill (Groq LLM)

Wrapped by: RalphWiggumLoop orchestrator
```

## 🔄 Execution Flow

```
1. Find Plan.md files in Plans/ folder
2. Decompose plan into executable tasks
3. Execute tasks loop:
   - Select next task (based on priority & dependencies)
   - Execute task using appropriate skill
   - Evaluate progress
   - Adjust plan if needed
   - Repeat until complete
4. Archive execution results
```

## 💰 Cost

**COMPLETELY FREE!** Uses Groq API with Llama 3.3 70B model.

- Cost: $0/month
- Get free API key: https://console.groq.com/keys
- Add to `.env`: `GROQ_API_KEY=your_key_here`

## 📦 Components

### Models
- **ExecutionState** - Tracks execution progress, tasks, evaluations
- **ExecutableTask** - Individual task with dependencies, retries, status
- **EvaluationResult** - Progress evaluation results

### Skills (5 skills)
1. **TaskDecomposer** (Groq) - Breaks Plan.md into executable tasks
2. **TaskSelector** (no LLM) - Selects next task based on priority
3. **TaskExecutor** (no LLM) - Executes tasks by calling skills
4. **ProgressEvaluator** (Groq) - Evaluates execution health
5. **PlanAdjuster** (Groq) - Adjusts plan based on evaluation

### Agent
- **ExecutionAgent** - Orchestrates the 5 skills (mirrors ReasoningAgent)

### Orchestrator
- **RalphWiggumLoop** - Runs ExecutionAgent on schedule (mirrors ReasoningLoopOrchestrator)

## 🚀 Usage

### Option 1: Run Once (Execute a Specific Plan)

```bash
cd /mnt/d/FTE_Employee/hackathon_zero

# Execute a specific plan
python src/agents/execution_agent.py \
  --vault ai_employee_vault \
  --plan ai_employee_vault/Plans/Plan_20260121_1200_EmailResponses.md

# With custom settings
python src/agents/execution_agent.py \
  --vault ai_employee_vault \
  --plan ai_employee_vault/Plans/Plan_20260121_1200_EmailResponses.md \
  --model llama-3.3-70b-versatile \
  --max-iterations 20 \
  --verbose
```

### Option 2: Run Continuous Loop (Autonomous Mode)

```bash
cd /mnt/d/FTE_Employee/hackathon_zero

# Run continuous loop (checks every 5 minutes)
python src/orchestrator/ralph_wiggum_loop.py \
  --vault ai_employee_vault \
  --interval 300

# Run once and exit
python src/orchestrator/ralph_wiggum_loop.py \
  --vault ai_employee_vault \
  --once

# Custom interval (check every 1 minute)
python src/orchestrator/ralph_wiggum_loop.py \
  --vault ai_employee_vault \
  --interval 60 \
  --verbose
```

## 📊 How It Works with the Reasoning Loop

### Complete System Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. WATCHERS (Data Collection)                          │
│    Gmail, LinkedIn, Instagram watchers                 │
│    ↓ Creates task files in Need_Action/                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. REASONING LOOP (Planning)                            │
│    ReasoningAgent + ReasoningLoopOrchestrator          │
│    ↓ Scans Need_Action/, creates Plan.md               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. RALPH WIGGUM LOOP (Execution) ← YOU ARE HERE        │
│    ExecutionAgent + RalphWiggumLoop                    │
│    ↓ Executes Plan.md, completes tasks                 │
└─────────────────────────────────────────────────────────┘
```

### Example Scenario

1. **Gmail Watcher** finds 3 urgent emails → Creates task files in `Need_Action/email_replies/`

2. **Reasoning Loop** (every 30 min):
   - Scans `Need_Action/`
   - Finds 3 email tasks
   - Creates `Plans/Plan_20260121_EmailResponses.md`

3. **Ralph Wiggum Loop** (every 5 min):
   - Finds `Plan_20260121_EmailResponses.md`
   - Decomposes into executable tasks:
     - Task 1: Classify email_001 (email_classifier skill)
     - Task 2: Classify email_002 (email_classifier skill)
     - Task 3: Classify email_003 (email_classifier skill)
     - Task 4: Draft responses (content_optimizer skill)
   - Executes tasks sequentially
   - Evaluates progress
   - Marks complete

## 📁 Output Files

### Execution State
- **Active execution**: `ExecutionState/active_execution.json`
- **Archived executions**: `ExecutionState/execution_history/execution_YYYYMMDD_HHMMSS_ID.json`

### Logs
- **Execution logs**: `Logs/execution_logs/execution_YYYYMMDD_HHMMSS.md`
- **Dashboard updates**: `Dashboard.md` (Ralph Wiggum Loop Status section)

## 🎯 Features

### Intelligent Task Decomposition
- Uses Groq LLM to break plans into executable tasks
- Maps actions to appropriate skills
- Identifies dependencies automatically
- Calculates priorities

### Dependency Management
- Respects task dependencies
- Executes tasks in correct order
- Detects circular dependencies

### Error Handling & Retry
- Automatic retry on failure (up to 3 attempts)
- Intelligent error recovery
- Graceful degradation

### Progress Evaluation
- LLM-powered progress assessment
- Identifies blocking issues
- Recommends adjustments

### Plan Adjustment
- Dynamically adjusts plan based on evaluation
- Can skip, retry, add, modify, or reorder tasks
- Learns from failures

### State Persistence
- Saves state after each iteration
- Resume interrupted executions
- Full execution history

## 🔧 Advanced Usage

### Resume Interrupted Execution

```bash
# If execution was interrupted, it will auto-resume
python src/orchestrator/ralph_wiggum_loop.py --vault ai_employee_vault --once

# Or manually resume via ExecutionAgent
python src/agents/execution_agent.py \
  --vault ai_employee_vault \
  --plan ai_employee_vault/Plans/Plan_XYZ.md \
  --resume
```

### Inspect Execution State

```bash
# View active execution
cat ai_employee_vault/ExecutionState/active_execution.json | jq

# View execution history
ls -lh ai_employee_vault/ExecutionState/execution_history/

# View execution logs
ls -lh ai_employee_vault/Logs/execution_logs/
```

### Run Both Loops Together

```bash
# Terminal 1: Reasoning Loop (creates plans)
python src/orchestrator/reasoning_loop.py \
  --vault ai_employee_vault \
  --interval 1800

# Terminal 2: Ralph Wiggum Loop (executes plans)
python src/orchestrator/ralph_wiggum_loop.py \
  --vault ai_employee_vault \
  --interval 300
```

## 📈 Monitoring

### Dashboard
Check `Dashboard.md` for latest execution status:
```markdown
## Ralph Wiggum Loop Status
- **Last Execution:** ✅ Email Response Plan - 3/3 tasks at 2026-01-21 15:30
```

### Logs
Detailed execution logs in `Logs/execution_logs/`:
```markdown
# Execution Summary: Email Response Plan

**Status:** ✅ COMPLETED
**Progress:** 3/3 tasks (100%)
**Iterations:** 1/10

## Task Breakdown
- ✅ Completed: 3
- ❌ Failed: 0
- ⏭️ Skipped: 0
- 📋 Pending: 0
```

## 🐛 Troubleshooting

### No Plans Found
```
❌ No pending plans to execute
```
**Solution**: Check if Reasoning Loop has created plans in `Plans/` folder

### GROQ_API_KEY Error
```
❌ GROQ_API_KEY not found
```
**Solution**: Add to `.env` file: `GROQ_API_KEY=your_key_here`

### Skill Not Found
```
❌ Skill 'xyz' not found
```
**Solution**: Check skill exists in `src/skills/` and is properly registered

### Circular Dependency
```
❌ Circular dependency detected: 5 tasks pending but none ready
```
**Solution**: Plan adjustment will automatically fix this, or manually edit the plan

## 🎓 Gold Tier Completion

With Ralph Wiggum Loop implemented, you've completed:

✅ **Autonomous Multi-Step Execution** - The loop executes complex tasks without human intervention
✅ **Self-Directed Goal Completion** - Breaks down goals, selects actions, executes, evaluates
✅ **Closed Feedback Loop** - Plan → Execute → Evaluate → Adjust → Repeat

**Gold Tier Progress**: ~60% complete! 🎉

### Remaining Gold Tier Items
- Weekly Business Audit
- Full Cross-Domain Integration
- Error Recovery (partially done via Ralph Loop)
- Comprehensive Audit Logging
- Complete social media summaries

## 🙏 Credits

Inspired by Ralph Wiggum from The Simpsons - always autonomous, always persistent, always helping!

**"I'm helping! I'm helping! I'm helping!"** 🤖
