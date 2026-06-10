"""
ProgressEvaluator Skill - Evaluates execution progress and determines if adjustments needed
Uses Groq LLM (FREE) for intelligent evaluation
"""
import json
import re
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from models.execution_state import ExecutionState, EvaluationResult, TaskStatus


class ProgressEvaluator(BaseSkill):
    """
    Evaluates execution progress using Groq LLM.

    Assesses:
    - Are we on track to achieve the goal?
    - Are failures critical or recoverable?
    - Are there blocking issues?
    - Should we adjust the plan?
    - Should we continue or abort?
    """

    SKILL_NAME = "progress_evaluator"
    REQUIRES_LLM = True
    DESCRIPTION = "Evaluates execution progress and determines if adjustments needed using Groq LLM (FREE)"

    def __init__(self, vault_path: str, groq_api_key: str, groq_model: str = "llama-3.3-70b-versatile", **kwargs):
        super().__init__(vault_path, groq_api_key=groq_api_key, groq_model=groq_model, **kwargs)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Evaluate execution progress.

        Input:
            data = {
                "execution_state": ExecutionState,
                "original_plan": str (plan content)
            }

        Output:
            result = EvaluationResult
        """
        try:
            execution_state = input_data.data.get("execution_state")
            original_plan = input_data.data.get("original_plan", "")

            if not execution_state:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Execution state not provided"
                )

            # Calculate metrics
            metrics = self._calculate_metrics(execution_state)

            # Use Groq LLM to evaluate
            evaluation = self._evaluate_with_llm(execution_state, metrics, original_plan)

            return SkillOutput(
                result=evaluation,
                success=True,
                metadata={
                    "execution_id": execution_state.execution_id,
                    "iteration": execution_state.iteration,
                    **metrics
                }
            )

        except Exception as e:
            return SkillOutput(
                result=None,
                success=False,
                error_message=f"Progress evaluation failed: {str(e)}"
            )

    def _calculate_metrics(self, state: ExecutionState) -> dict:
        """Calculate progress metrics"""
        total = len(state.tasks)
        completed = sum(1 for t in state.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in state.tasks if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in state.tasks if t.status == TaskStatus.SKIPPED)
        pending = sum(1 for t in state.tasks if t.status == TaskStatus.PENDING)
        blocked = sum(1 for t in state.tasks if t.status == TaskStatus.BLOCKED)

        completed_pct = (completed / total * 100) if total > 0 else 0
        failed_pct = (failed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": pending,
            "blocked": blocked,
            "completed_pct": round(completed_pct, 1),
            "failed_pct": round(failed_pct, 1),
            "success_rate": round((completed / (completed + failed) * 100) if (completed + failed) > 0 else 0, 1)
        }

    def _evaluate_with_llm(self, state: ExecutionState, metrics: dict, original_plan: str) -> EvaluationResult:
        """Use Groq LLM to evaluate progress"""

        # Get recent task summaries
        recent_tasks = self._get_recent_task_summaries(state)

        system_prompt = """You are an execution progress evaluator. Assess if execution is on track and if adjustments are needed.

Evaluation Criteria:
- on_track: Are we making good progress toward the goal?
- confidence: "high", "medium", or "low" based on progress quality
- needs_adjustment: Should we modify the plan to overcome issues?
- blocking_issues: List specific problems preventing progress
- recommendations: List actionable suggestions
- should_continue: Should we continue execution or stop?

Return ONLY a JSON object with these fields:
{
  "on_track": boolean,
  "confidence": "high" | "medium" | "low",
  "needs_adjustment": boolean,
  "blocking_issues": [strings],
  "recommendations": [strings],
  "should_continue": boolean,
  "reasoning": "brief explanation"
}"""

        user_prompt = f"""Evaluate execution progress:

Goal: {state.goal}
Iteration: {state.iteration}/{state.max_iterations}

Progress Metrics:
- Completed: {metrics['completed']}/{metrics['total']} ({metrics['completed_pct']}%)
- Failed: {metrics['failed']} ({metrics['failed_pct']}%)
- Pending: {metrics['pending']}
- Blocked: {metrics['blocked']}
- Success Rate: {metrics['success_rate']}%

Recent Tasks:
{json.dumps(recent_tasks, indent=2)}

Original Plan Summary:
{original_plan[:500]}...

Assess if we're on track, identify issues, and recommend if adjustments are needed."""

        # Call Groq LLM
        response = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        # Extract JSON from response
        evaluation_data = self._extract_json(response)

        # Create EvaluationResult
        evaluation = EvaluationResult(
            on_track=evaluation_data.get("on_track", True),
            confidence=evaluation_data.get("confidence", "medium"),
            needs_adjustment=evaluation_data.get("needs_adjustment", False),
            blocking_issues=evaluation_data.get("blocking_issues", []),
            recommendations=evaluation_data.get("recommendations", []),
            should_continue=evaluation_data.get("should_continue", True),
            reasoning=evaluation_data.get("reasoning", ""),
            metrics=metrics
        )

        return evaluation

    def _get_recent_task_summaries(self, state: ExecutionState, limit: int = 5) -> list:
        """Get summaries of recent tasks for LLM context"""
        summaries = []

        # Get last N tasks (by update time)
        sorted_tasks = sorted(
            state.tasks,
            key=lambda t: t.updated_at,
            reverse=True
        )[:limit]

        for task in sorted_tasks:
            summaries.append({
                "id": task.id,
                "action": task.action,
                "status": task.status.value,
                "skill": task.skill_name,
                "attempts": task.attempts,
                "error": task.error_message if task.error_message else None
            })

        return summaries

    def _extract_json(self, response: str) -> dict:
        """Extract JSON object from LLM response"""
        # Try to find JSON object in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Fallback: return conservative evaluation
        return {
            "on_track": True,
            "confidence": "medium",
            "needs_adjustment": False,
            "blocking_issues": [],
            "recommendations": [],
            "should_continue": True,
            "reasoning": "Unable to parse LLM evaluation, defaulting to continue"
        }
