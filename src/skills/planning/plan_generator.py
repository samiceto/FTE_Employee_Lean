"""
PlanGenerator Skill - Generates action plans using Groq LLM
Extracted from reasoning_agent.py (lines 175-425)
"""
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from ..base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    """Represents a generated plan"""
    title: str
    summary: str
    reasoning: str
    steps: list[dict]
    estimated_complexity: str
    dependencies: list[str]
    risks: list[str]
    success_criteria: list[str]
    created_at: datetime = field(default_factory=datetime.now)


class PlanGenerator(BaseSkill):
    """
    Generates action plans using Groq LLM.

    This skill takes a list of tasks and business context, then uses
    the FREE Groq API to reason about them and create a detailed Plan.md file.

    USES Groq API - Free but requires API key.
    """

    SKILL_NAME = "plan_generator"
    REQUIRES_LLM = True
    DESCRIPTION = "Generate action plans from tasks using Groq LLM"

    SYSTEM_PROMPT = """You are an AI business analyst and planner working as part of an automated employee system.
Your role is to analyze incoming tasks, emails, and requests, then create detailed actionable plans.

When analyzing tasks, consider:
1. The urgency and priority of the task
2. Dependencies on other tasks or external factors
3. Potential risks and mitigation strategies
4. Clear success criteria
5. Step-by-step actionable items

You have access to the business context:
- This is a freelance/consulting business
- Revenue target: $10,000/month
- Key metrics: Client response time (<24h), Invoice payment rate (>90%)
- The system has automated posting capabilities for LinkedIn, Instagram, and X

Always provide structured, actionable plans that can be executed by both humans and automated systems."""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Generate a plan from tasks and business context.

        Args:
            input_data: SkillInput with:
                - data: dict containing "tasks" (list of TaskItem objects)
                - context: dict containing "business_context" (string)

        Returns:
            SkillOutput with Plan object and saved plan path
        """
        # Validate input
        error = self.validate_input(input_data, ["tasks"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            tasks = input_data.data["tasks"]
            business_context = input_data.context.get("business_context", "")

            if not tasks:
                logger.info("No tasks to process")
                return SkillOutput(
                    result=None,
                    success=True,
                    metadata={"reason": "no_tasks"}
                )

            # Generate plan using Groq
            plan = self._reason_and_plan(tasks, business_context)
            if not plan:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Failed to generate plan from LLM"
                )

            # Save plan to disk
            plan_path = self._save_plan(plan)

            return SkillOutput(
                result=plan,
                success=True,
                metadata={
                    "plan_path": str(plan_path),
                    "task_count": len(tasks),
                    "step_count": len(plan.steps)
                }
            )

        except Exception as e:
            logger.error(f"PlanGenerator execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _build_reasoning_prompt(self, tasks: list, business_context: str) -> str:
        """Build the prompt for LLM to reason about tasks"""
        task_summaries = []

        for i, task in enumerate(tasks, 1):
            task_summary = f"""
### Task {i}: {task.file_path.name}
- **Type:** {task.task_type}
- **Priority:** {task.priority}
- **Metadata:** {json.dumps(task.metadata, default=str)}

**Content:**
{task.content[:300]}{"..." if len(task.content) > 300 else ""}
"""
            task_summaries.append(task_summary)

        return f"""# Business Context
{business_context}

# Pending Tasks ({len(tasks)} items)
{"".join(task_summaries)}

# Your Task
Analyze these pending tasks and create a comprehensive action plan. Consider:

1. **Task Prioritization:** Which tasks need immediate attention?
2. **Task Grouping:** Can any tasks be batched together?
3. **Dependencies:** What needs to happen before other tasks can proceed?
4. **Automation Opportunities:** Which tasks can be fully automated vs need human review?
5. **Risk Assessment:** What could go wrong and how to mitigate?

Provide your plan in the following JSON structure:
```json
{{
    "title": "Plan title summarizing the main focus",
    "summary": "2-3 sentence executive summary",
    "reasoning": "Your detailed reasoning process (what you considered, why you made certain decisions)",
    "steps": [
        {{
            "order": 1,
            "action": "Specific action to take",
            "task_refs": ["task filenames this relates to"],
            "assignee": "human|automated|hybrid",
            "details": "Additional details or context",
            "estimated_effort": "low|medium|high"
        }}
    ],
    "estimated_complexity": "simple|moderate|complex",
    "dependencies": ["List of external dependencies"],
    "risks": ["Potential risks to be aware of"],
    "success_criteria": ["How to know when this plan is complete"]
}}
```"""

    def _reason_and_plan(self, tasks: list, business_context: str) -> Optional[Plan]:
        """Use Groq LLM to reason about tasks and generate a plan"""
        prompt = self._build_reasoning_prompt(tasks, business_context)

        try:
            # Add chain-of-thought instruction for better reasoning
            thinking_instruction = """Think through this step-by-step before providing your final answer:
1. Analyze the problem thoroughly
2. Consider different approaches
3. Reason through your solution
4. Provide your final structured response

Format your response as:
<thinking>
Your step-by-step reasoning here...
</thinking>

<answer>
Your final JSON answer here...
</answer>"""

            full_prompt = f"{thinking_instruction}\n\n---\n\n{prompt}"

            # Call Groq API
            content = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=full_prompt,
                temperature=0.7,
                max_tokens=8000
            )

            thinking = None

            # Extract thinking from response if present
            if "<thinking>" in content and "</thinking>" in content:
                thinking_start = content.find("<thinking>") + len("<thinking>")
                thinking_end = content.find("</thinking>")
                thinking = content[thinking_start:thinking_end].strip()

                # Extract answer
                if "<answer>" in content and "</answer>" in content:
                    answer_start = content.find("<answer>") + len("<answer>")
                    answer_end = content.find("</answer>")
                    content = content[answer_start:answer_end].strip()
                else:
                    # Remove thinking section from content
                    content = content[content.find("</thinking>") + len("</thinking>"):].strip()

            # Log the thinking process if available
            if thinking:
                self._log_thinking(thinking, tasks)

            # Parse the JSON response
            plan_data = self._extract_json_from_response(content)
            if not plan_data:
                logger.error("Failed to extract plan JSON from response")
                logger.debug(f"Response content: {content[:500]}...")
                return None

            return Plan(
                title=plan_data.get("title", "Untitled Plan"),
                summary=plan_data.get("summary", ""),
                reasoning=plan_data.get("reasoning", thinking or ""),
                steps=plan_data.get("steps", []),
                estimated_complexity=plan_data.get("estimated_complexity", "moderate"),
                dependencies=plan_data.get("dependencies", []),
                risks=plan_data.get("risks", []),
                success_criteria=plan_data.get("success_criteria", [])
            )

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _extract_json_from_response(self, response: str) -> Optional[dict]:
        """Extract JSON from LLM response"""
        # Try to find JSON in code block
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        try:
            # Find the first { and last }
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return None

    def _log_thinking(self, thinking: str, tasks: list) -> None:
        """Log LLM's thinking process for debugging and auditing"""
        vault_path = Path(self.vault_path)
        logs_dir = vault_path / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"reasoning_{timestamp}.md"

        task_names = [t.file_path.name for t in tasks]

        log_content = f"""# Reasoning Log - {timestamp}

## Model
Groq - {self.groq_model}

## Tasks Analyzed
{json.dumps(task_names, indent=2)}

## LLM Thinking Process
{thinking}

---
Generated at: {datetime.now().isoformat()}
"""
        log_file.write_text(log_content, encoding="utf-8")
        logger.info(f"Thinking log saved to {log_file}")

    def _generate_plan_markdown(self, plan: Plan) -> str:
        """Convert a Plan object to markdown format"""
        steps_md = ""
        for step in plan.steps:
            assignee_icon = {
                "human": "👤",
                "automated": "🤖",
                "hybrid": "🤝"
            }.get(step.get("assignee", "human"), "👤")

            steps_md += f"""
### Step {step.get('order', '?')}: {step.get('action', 'Unknown')}
- **Assignee:** {assignee_icon} {step.get('assignee', 'human')}
- **Effort:** {step.get('estimated_effort', 'unknown')}
- **Related Tasks:** {', '.join(step.get('task_refs', []))}

{step.get('details', '')}
"""

        return f"""---
title: "{plan.title}"
created: {plan.created_at.isoformat()}
complexity: {plan.estimated_complexity}
status: pending
model: {self.groq_model}
---

# {plan.title}

## Summary
{plan.summary}

## Reasoning
{plan.reasoning}

## Action Steps
{steps_md}

## Dependencies
{chr(10).join(f'- {d}' for d in plan.dependencies) if plan.dependencies else '- None identified'}

## Risks
{chr(10).join(f'- ⚠️ {r}' for r in plan.risks) if plan.risks else '- None identified'}

## Success Criteria
{chr(10).join(f'- ✅ {c}' for c in plan.success_criteria) if plan.success_criteria else '- Plan completion'}

---
*Generated by Groq ({self.groq_model}) at {plan.created_at.isoformat()}*
"""

    def _save_plan(self, plan: Plan) -> Path:
        """Save a plan to the Plans directory"""
        vault_path = Path(self.vault_path)
        plans_dir = vault_path / "Plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        timestamp = plan.created_at.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in plan.title)
        safe_title = safe_title.replace(" ", "_")[:50]

        filename = f"Plan_{timestamp}_{safe_title}.md"
        plan_path = plans_dir / filename

        markdown = self._generate_plan_markdown(plan)
        plan_path.write_text(markdown, encoding="utf-8")

        logger.info(f"Plan saved to {plan_path}")
        return plan_path
