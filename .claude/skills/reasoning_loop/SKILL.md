# Skill: Claude Reasoning Loop

## Objective
Analyze pending tasks in `/Need_Action` using Claude's extended thinking capabilities and generate comprehensive `Plan.md` files in `/Plans`.

## When to Use
- When there are new items in `/Need_Action` that need analysis
- When the user requests a plan for pending tasks
- Periodically via the orchestrator (every 30 minutes by default)

## Steps
1. **Collect Tasks**: Scan `/Need_Action` and its subfolders for `.md` files
2. **Load Context**: Read `Business_Goals.md` and `Company_Handbook.md` for business context
3. **Analyze with Claude**: Send tasks to Claude API with extended thinking enabled
4. **Generate Plan**: Create structured `Plan.md` with:
   - Executive summary
   - Detailed reasoning
   - Prioritized action steps (human/automated/hybrid)
   - Dependencies and risks
   - Success criteria
5. **Save Plan**: Write to `/Plans/Plan_YYYYMMDD_HHMMSS_Title.md`
6. **Log Thinking**: Save Claude's thinking process to `/Logs/reasoning_*.md`
7. **Update Dashboard**: Update `Dashboard.md` with latest plan status

## Configuration
- **Interval**: 30 minutes (configurable via `--interval`)
- **Cooldown**: 60 minutes after plan generation
- **Minimum Tasks**: 1 (configurable via `--min-tasks`)
- **Model**: claude-sonnet-4-20250514 (supports extended thinking)

## Environment Requirements
- `ANTHROPIC_API_KEY` must be set in `.env` or environment

## Commands
```bash
# Run once
python src/agents/reasoning_agent.py --vault /path/to/vault

# Run continuous loop
python src/orchestrator/reasoning_loop.py --vault /path/to/vault

# Run with PM2
pm2 start ecosystem.config.js --only reasoning-loop
```

## Output Format
Plans are generated in markdown with YAML frontmatter:
```markdown
---
title: "Plan Title"
created: 2026-01-18T10:30:00
complexity: moderate
status: pending
---
# Plan Title
## Summary
## Reasoning
## Action Steps
## Dependencies
## Risks
## Success Criteria
```

## Constraints
- Requires valid Anthropic API key
- Extended thinking requires compatible model (claude-sonnet-4 or claude-opus-4)
- Plans are suggestions - human approval recommended for sensitive actions
