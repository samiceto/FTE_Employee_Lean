"""
TaskSelector Skill - Selects next task to execute based on priority and dependencies
No LLM required - pure logic
"""
from pathlib import Path
from typing import List, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from models.execution_state import ExecutableTask, TaskStatus, ExecutionState


class TaskSelector(BaseSkill):
    """
    Selects the next task to execute based on:
    - Task status (only PENDING)
    - Dependencies (all must be COMPLETED)
    - Priority (higher priority first)
    - Order (earlier tasks first when priority equal)
    """

    SKILL_NAME = "task_selector"
    REQUIRES_LLM = False
    DESCRIPTION = "Selects next task based on priority and dependencies"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Select next task to execute.

        Input:
            data = {
                "tasks": List[ExecutableTask]
            }
            context = {
                "execution_state": ExecutionState (optional)
            }

        Output:
            result = ExecutableTask or None
        """
        try:
            tasks = input_data.data.get("tasks", [])

            if not tasks:
                return SkillOutput(
                    result=None,
                    success=True,
                    metadata={"message": "No tasks provided"}
                )

            # Get execution state from context if available
            execution_state = input_data.context.get("execution_state")

            # Get completed task IDs
            if execution_state:
                completed_ids = execution_state.get_completed_task_ids()
            else:
                completed_ids = {t.id for t in tasks if t.status == TaskStatus.COMPLETED}

            # Filter to tasks ready to execute
            ready_tasks = self._get_ready_tasks(tasks, completed_ids)

            if not ready_tasks:
                # Check if all pending but none ready (circular dependency)
                pending = [t for t in tasks if t.status == TaskStatus.PENDING]
                if pending:
                    return SkillOutput(
                        result=None,
                        success=False,
                        error_message=f"Circular dependency detected: {len(pending)} tasks pending but none ready"
                    )
                else:
                    return SkillOutput(
                        result=None,
                        success=True,
                        metadata={"message": "No tasks ready to execute"}
                    )

            # Select highest priority task
            selected_task = self._select_highest_priority(ready_tasks)

            return SkillOutput(
                result=selected_task,
                success=True,
                metadata={
                    "selected_task_id": selected_task.id,
                    "ready_tasks_count": len(ready_tasks),
                    "total_tasks": len(tasks)
                }
            )

        except Exception as e:
            return SkillOutput(
                result=None,
                success=False,
                error_message=f"Task selection failed: {str(e)}"
            )

    def _get_ready_tasks(self, tasks: List[ExecutableTask], completed_ids: set) -> List[ExecutableTask]:
        """Get tasks that are ready to execute"""
        ready = []

        for task in tasks:
            # Only PENDING tasks
            if task.status != TaskStatus.PENDING:
                continue

            # Check all dependencies are completed
            if all(dep_id in completed_ids for dep_id in task.dependencies):
                ready.append(task)

        return ready

    def _select_highest_priority(self, tasks: List[ExecutableTask]) -> ExecutableTask:
        """Select task with highest priority, breaking ties by task ID order"""
        if not tasks:
            return None

        # Sort by priority (descending), then by task ID (ascending)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-t.priority, self._extract_task_number(t.id))
        )

        return sorted_tasks[0]

    def _extract_task_number(self, task_id: str) -> int:
        """Extract numeric order from task ID (e.g., 'task_3' -> 3)"""
        try:
            # Assumes task IDs like "task_1", "task_2", etc.
            parts = task_id.split('_')
            return int(parts[-1])
        except:
            return 0
