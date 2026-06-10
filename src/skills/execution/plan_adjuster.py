"""
PlanAdjuster Skill - Adjusts execution plan based on evaluation results
Uses Groq LLM (FREE) for intelligent adjustments
"""
import json
import re
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from models.execution_state import ExecutionState, EvaluationResult, ExecutableTask, TaskStatus


class PlanAdjuster(BaseSkill):
    """
    Adjusts execution plan based on evaluation results.

    Adjustment Types:
    - SKIP: Mark non-critical failed tasks as SKIPPED
    - RETRY: Reset failed task with modified parameters
    - ADD: Insert new tasks to unblock progress
    - MODIFY: Update task parameters or skill mapping
    - REORDER: Change task priorities
    """

    SKILL_NAME = "plan_adjuster"
    REQUIRES_LLM = True
    DESCRIPTION = "Adjusts execution plan based on evaluation results using Groq LLM (FREE)"

    def __init__(self, vault_path: str, groq_api_key: str, groq_model: str = "llama-3.3-70b-versatile", **kwargs):
        super().__init__(vault_path, groq_api_key=groq_api_key, groq_model=groq_model, **kwargs)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Adjust execution plan.

        Input:
            data = {
                "execution_state": ExecutionState,
                "evaluation": EvaluationResult,
                "original_plan": str (optional)
            }

        Output:
            result = Updated ExecutionState
        """
        try:
            execution_state = input_data.data.get("execution_state")
            evaluation = input_data.data.get("evaluation")
            original_plan = input_data.data.get("original_plan", "")

            if not execution_state:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Execution state not provided"
                )

            if not evaluation:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Evaluation result not provided"
                )

            # If no adjustment needed, return state unchanged
            if not evaluation.needs_adjustment:
                return SkillOutput(
                    result=execution_state,
                    success=True,
                    metadata={"message": "No adjustment needed"}
                )

            # Use Groq LLM to generate adjustments
            adjustments = self._generate_adjustments_with_llm(
                execution_state,
                evaluation,
                original_plan
            )

            # Apply adjustments
            updated_state = self._apply_adjustments(execution_state, adjustments)

            # Record adjustments
            updated_state.adjustments_made.append({
                "timestamp": datetime.now().isoformat(),
                "iteration": updated_state.iteration,
                "adjustments": adjustments
            })

            return SkillOutput(
                result=updated_state,
                success=True,
                metadata={
                    "adjustments_count": len(adjustments),
                    "adjustments": adjustments
                }
            )

        except Exception as e:
            return SkillOutput(
                result=execution_state if 'execution_state' in locals() else None,
                success=False,
                error_message=f"Plan adjustment failed: {str(e)}"
            )

    def _generate_adjustments_with_llm(self, state: ExecutionState, evaluation: EvaluationResult, original_plan: str) -> list:
        """Use Groq LLM to generate adjustment plan"""

        # Get problematic tasks
        failed_tasks = [t for t in state.tasks if t.status == TaskStatus.FAILED]
        blocked_tasks = [t for t in state.tasks if t.status == TaskStatus.BLOCKED]

        system_prompt = """You are a plan adjustment expert. Generate adjustments to overcome execution issues.

Adjustment Types:
1. SKIP - Skip non-critical failed task
   {"type": "skip", "task_id": "task_X", "reason": "..."}

2. RETRY - Retry failed task with new parameters
   {"type": "retry", "task_id": "task_X", "new_skill_input": {...}}

3. ADD - Add new task to unblock progress
   {"type": "add", "action": "...", "skill_name": "...", "skill_input": {...}, "priority": N, "dependencies": [...]}

4. MODIFY - Change task parameters
   {"type": "modify", "task_id": "task_X", "changes": {"skill_name": "...", "skill_input": {...}}}

5. REORDER - Change task priority
   {"type": "reorder", "task_id": "task_X", "new_priority": N}

Return ONLY a JSON array of adjustments, no other text."""

        user_prompt = f"""Goal: {state.goal}

Blocking Issues:
{json.dumps(evaluation.blocking_issues, indent=2)}

Recommendations:
{json.dumps(evaluation.recommendations, indent=2)}

Failed Tasks:
{json.dumps([{"id": t.id, "action": t.action, "skill": t.skill_name, "error": t.error_message} for t in failed_tasks], indent=2)}

Blocked Tasks:
{json.dumps([{"id": t.id, "action": t.action, "reason": t.error_message} for t in blocked_tasks], indent=2)}

Generate adjustments to overcome these issues and continue progress."""

        # Call Groq LLM
        response = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        # Extract JSON array from response
        adjustments = self._extract_json_array(response)

        return adjustments

    def _apply_adjustments(self, state: ExecutionState, adjustments: list) -> ExecutionState:
        """Apply adjustments to execution state"""
        for adjustment in adjustments:
            adj_type = adjustment.get("type")

            if adj_type == "skip":
                self._apply_skip(state, adjustment)
            elif adj_type == "retry":
                self._apply_retry(state, adjustment)
            elif adj_type == "add":
                self._apply_add(state, adjustment)
            elif adj_type == "modify":
                self._apply_modify(state, adjustment)
            elif adj_type == "reorder":
                self._apply_reorder(state, adjustment)

        # Update progress after adjustments
        state.update_progress()

        return state

    def _apply_skip(self, state: ExecutionState, adjustment: dict):
        """Skip a task"""
        task_id = adjustment.get("task_id")
        reason = adjustment.get("reason", "Skipped due to adjustment")

        task = self._find_task(state, task_id)
        if task:
            task.mark_skipped(reason)

    def _apply_retry(self, state: ExecutionState, adjustment: dict):
        """Retry a task with new parameters"""
        task_id = adjustment.get("task_id")
        new_skill_input = adjustment.get("new_skill_input", {})

        task = self._find_task(state, task_id)
        if task:
            # Reset task to pending with new parameters
            task.status = TaskStatus.PENDING
            task.skill_input.update(new_skill_input)
            task.attempts = 0  # Reset attempts
            task.error_message = None
            task.updated_at = datetime.now().isoformat()

    def _apply_add(self, state: ExecutionState, adjustment: dict):
        """Add a new task"""
        # Generate unique task ID
        max_task_num = max(
            (self._extract_task_number(t.id) for t in state.tasks),
            default=0
        )
        new_task_id = f"task_{max_task_num + 1}"

        new_task = ExecutableTask(
            id=new_task_id,
            action=adjustment.get("action", "New task"),
            skill_name=adjustment.get("skill_name", "unknown"),
            skill_input=adjustment.get("skill_input", {}),
            priority=adjustment.get("priority", 5),
            dependencies=adjustment.get("dependencies", []),
            status=TaskStatus.PENDING
        )

        state.tasks.append(new_task)

    def _apply_modify(self, state: ExecutionState, adjustment: dict):
        """Modify a task"""
        task_id = adjustment.get("task_id")
        changes = adjustment.get("changes", {})

        task = self._find_task(state, task_id)
        if task:
            if "skill_name" in changes:
                task.skill_name = changes["skill_name"]
            if "skill_input" in changes:
                task.skill_input.update(changes["skill_input"])
            if "priority" in changes:
                task.priority = changes["priority"]
            task.updated_at = datetime.now().isoformat()

    def _apply_reorder(self, state: ExecutionState, adjustment: dict):
        """Reorder task priority"""
        task_id = adjustment.get("task_id")
        new_priority = adjustment.get("new_priority", 5)

        task = self._find_task(state, task_id)
        if task:
            task.priority = new_priority
            task.updated_at = datetime.now().isoformat()

    def _find_task(self, state: ExecutionState, task_id: str) -> ExecutableTask:
        """Find task by ID"""
        for task in state.tasks:
            if task.id == task_id:
                return task
        return None

    def _extract_task_number(self, task_id: str) -> int:
        """Extract numeric order from task ID"""
        try:
            parts = task_id.split('_')
            return int(parts[-1])
        except:
            return 0

    def _extract_json_array(self, response: str) -> list:
        """Extract JSON array from LLM response"""
        # Try to find JSON array in response
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing entire response
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback: no adjustments
        return []
