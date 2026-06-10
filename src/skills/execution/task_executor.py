"""
TaskExecutor Skill - Executes tasks by calling appropriate skills
Handles errors, retries, and result tracking
"""
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from models.execution_state import ExecutableTask, TaskStatus

logger = logging.getLogger(__name__)


class TaskExecutor(BaseSkill):
    """
    Executes tasks by:
    - Getting skill instance from registry
    - Preparing skill input
    - Calling skill.execute()
    - Handling results and errors
    - Implementing retry logic
    """

    SKILL_NAME = "task_executor"
    REQUIRES_LLM = False
    DESCRIPTION = "Executes tasks by calling appropriate skills with error handling"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute a task.

        Input:
            data = {
                "task": ExecutableTask
            }
            context = {
                "skill_registry": registry instance (required),
                "vault_path": path to vault,
                "groq_api_key": Groq API key (for LLM skills),
                "groq_model": Groq model name
            }

        Output:
            result = Updated ExecutableTask
        """
        try:
            task = input_data.data.get("task")

            if not task:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="No task provided"
                )

            skill_registry = input_data.context.get("skill_registry")

            if not skill_registry:
                return SkillOutput(
                    result=task,
                    success=False,
                    error_message="Skill registry not provided in context"
                )

            # Mark task as in progress
            task.mark_in_progress()

            # Execute task
            execution_result = self._execute_task(task, skill_registry, input_data.context)

            if execution_result["success"]:
                # Mark task as completed
                task.mark_completed(
                    result=execution_result["result"],
                    metadata=execution_result.get("metadata", {})
                )
                logger.info(f"✅ Task {task.id} completed: {task.action}")

                return SkillOutput(
                    result=task,
                    success=True,
                    metadata={
                        "task_id": task.id,
                        "status": "completed"
                    }
                )
            else:
                # Mark task as failed (will retry if attempts < max_attempts)
                task.mark_failed(execution_result["error"])
                logger.warning(f"❌ Task {task.id} failed (attempt {task.attempts}/{task.max_attempts}): {execution_result['error']}")

                return SkillOutput(
                    result=task,
                    success=False,
                    error_message=execution_result["error"],
                    metadata={
                        "task_id": task.id,
                        "status": "failed" if task.status == TaskStatus.FAILED else "retry",
                        "attempts": task.attempts
                    }
                )

        except Exception as e:
            logger.error(f"Task execution error: {str(e)}", exc_info=True)
            return SkillOutput(
                result=task if 'task' in locals() else None,
                success=False,
                error_message=f"Task execution failed: {str(e)}"
            )

    def _execute_task(self, task: ExecutableTask, skill_registry, context: dict) -> dict:
        """Execute task using appropriate skill"""
        try:
            # Get skill instance
            skill_kwargs = {
                "vault_path": context.get("vault_path"),
                "groq_api_key": context.get("groq_api_key"),
                "groq_model": context.get("groq_model")
            }

            # Filter out None values
            skill_kwargs = {k: v for k, v in skill_kwargs.items() if v is not None}

            try:
                skill = skill_registry.get_skill(task.skill_name, **skill_kwargs)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Skill '{task.skill_name}' not found: {str(e)}"
                }

            # Prepare skill input
            skill_input = SkillInput(
                data=task.skill_input,
                context=context
            )

            # Execute skill
            logger.info(f"🔄 Executing task {task.id} with skill '{task.skill_name}'")
            skill_result = skill.execute(skill_input)

            if skill_result.success:
                return {
                    "success": True,
                    "result": skill_result.result,
                    "metadata": skill_result.metadata
                }
            else:
                return {
                    "success": False,
                    "error": skill_result.error_message or "Skill execution failed"
                }

        except Exception as e:
            logger.error(f"Error executing task {task.id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
