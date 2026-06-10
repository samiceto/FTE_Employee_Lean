"""
Groq Execution Agent - Executes Plan.md files using Groq LLM
Mirrors the structure of ReasoningAgent for consistency

Uses modular skill system with 5 execution skills:
- TaskDecomposer: Break plans into executable tasks
- TaskSelector: Choose next task based on dependencies
- TaskExecutor: Execute tasks using appropriate skills
- ProgressEvaluator: Assess execution health
- PlanAdjuster: Adjust plan based on evaluation

Uses Groq's ultra-fast FREE inference with Llama 3.3 70B model.
Get your free API key at: https://console.groq.com/keys
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from dotenv import load_dotenv

# Add parent directory to path for skills import
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import get_registry, SkillInput
from models.execution_state import (
    ExecutionState,
    ExecutionPhase,
    TaskStatus,
    EvaluationResult
)

load_dotenv()

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """
    Groq-powered execution agent that executes Plan.md files autonomously.

    Architecture mirrors ReasoningAgent for consistency.
    Uses modular skill system with auto-discovery.
    """

    def __init__(
        self,
        vault_path: str,
        model: str = "llama-3.3-70b-versatile",
        api_key: Optional[str] = None,
        max_iterations: int = 10,
        max_tasks_per_iteration: int = 10
    ):
        self.vault_path = Path(vault_path)
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.max_iterations = max_iterations
        self.max_tasks_per_iteration = max_tasks_per_iteration

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Get your free key at: https://console.groq.com/keys"
            )

        # Get the global skill registry
        self.registry = get_registry()

        # Auto-discover skills from the skills directory
        skills_path = Path(__file__).parent.parent / "skills"
        discovered = self.registry.auto_discover(skills_path)
        logger.info(f"Discovered {discovered} skills")

        # Initialize skill instances with shared parameters
        skill_kwargs = {
            "vault_path": str(self.vault_path),
            "groq_api_key": self.api_key,
            "groq_model": self.model
        }

        # Get execution skill instances
        self.task_decomposer = self.registry.get_skill("task_decomposer", **skill_kwargs)
        self.task_selector = self.registry.get_skill("task_selector", **skill_kwargs)
        self.task_executor = self.registry.get_skill("task_executor", **skill_kwargs)
        self.progress_evaluator = self.registry.get_skill("progress_evaluator", **skill_kwargs)
        self.plan_adjuster = self.registry.get_skill("plan_adjuster", **skill_kwargs)

        logger.info(f"Initialized execution agent with {self.model} and skill system")
        logger.info(f"Available skills: {list(self.registry.list_skills().keys())}")

    def execute_plan(self, plan_path: Path, resume: bool = False) -> ExecutionState:
        """
        Execute a plan file autonomously.

        This is the main entry point, mirrors ReasoningAgent.run_once()

        Args:
            plan_path: Path to Plan.md file
            resume: Whether to resume existing execution

        Returns:
            ExecutionState with results
        """
        logger.info(f"Starting execution agent for plan: {plan_path}")

        # Initialize or resume execution state
        if resume:
            state = ExecutionState.load(self.vault_path)
            if state:
                logger.info(f"Resuming execution: {state.execution_id}")
            else:
                logger.info("No existing execution found, starting new")
                state = self._initialize_execution(plan_path)
        else:
            state = self._initialize_execution(plan_path)

        # Main execution loop (Plan → Execute → Evaluate → Adjust → Repeat)
        while state.is_running and state.iteration < self.max_iterations:
            state.iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"ITERATION {state.iteration}/{self.max_iterations}")
            logger.info(f"{'='*60}")

            try:
                # Phase 1: Decompose (only on first iteration)
                if state.iteration == 1 and not state.tasks:
                    state = self._decompose_phase(state, plan_path)

                # Phase 2: Execute tasks
                state = self._execute_phase(state)

                # Phase 3: Evaluate progress
                state, evaluation = self._evaluate_phase(state, plan_path)

                # Phase 4: Adjust if needed
                if evaluation and evaluation.needs_adjustment:
                    state = self._adjust_phase(state, evaluation, plan_path)

                # Check completion
                if state.is_complete():
                    logger.info("✅ All tasks completed")
                    state.mark_completed()
                    break

                # Check if we should continue
                if evaluation and not evaluation.should_continue:
                    logger.warning("⚠️ Evaluation recommends stopping")
                    state.mark_failed("Stopped based on evaluation recommendation")
                    break

                # Save state after each iteration
                state.save(self.vault_path)

            except Exception as e:
                logger.error(f"Error in iteration {state.iteration}: {e}", exc_info=True)
                state.mark_failed(f"Error in iteration {state.iteration}: {str(e)}")
                break

        # Finalize execution
        return self._finalize_execution(state)

    def _initialize_execution(self, plan_path: Path) -> ExecutionState:
        """Initialize execution state"""
        logger.info("Initializing new execution")

        # Read plan to extract goal
        plan_content = plan_path.read_text()
        goal = self._extract_goal(plan_content)

        # Create execution state
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        state = ExecutionState(
            execution_id=execution_id,
            plan_path=str(plan_path),
            goal=goal,
            phase=ExecutionPhase.PLANNING,
            max_iterations=self.max_iterations
        )

        logger.info(f"Created execution: {execution_id}")
        logger.info(f"Goal: {goal}")

        return state

    def _decompose_phase(self, state: ExecutionState, plan_path: Path) -> ExecutionState:
        """Decompose plan into executable tasks"""
        logger.info("\n📋 PHASE: DECOMPOSITION")
        state.phase = ExecutionPhase.DECOMPOSING

        decomposer_input = SkillInput(
            data={"plan_path": str(plan_path)},
            context={"skill_registry": self.registry}
        )

        result = self.task_decomposer.execute(decomposer_input)

        if not result.success:
            logger.error(f"Decomposition failed: {result.error_message}")
            state.mark_failed(f"Decomposition failed: {result.error_message}")
            return state

        state.tasks = result.result
        state.update_progress()

        logger.info(f"✅ Decomposed into {len(state.tasks)} tasks")
        for task in state.tasks[:5]:  # Show first 5
            logger.info(f"  - {task.id}: {task.action} ({task.skill_name})")

        return state

    def _execute_phase(self, state: ExecutionState) -> ExecutionState:
        """Execute tasks batch"""
        logger.info("\n⚙️ PHASE: EXECUTION")
        state.phase = ExecutionPhase.EXECUTING

        tasks_executed = 0

        # Execute up to max_tasks_per_iteration
        while tasks_executed < self.max_tasks_per_iteration:
            # Select next task
            selector_input = SkillInput(
                data={"tasks": state.tasks},
                context={"execution_state": state}
            )

            select_result = self.task_selector.execute(selector_input)

            if not select_result.success or not select_result.result:
                logger.info("No more tasks ready to execute")
                break

            next_task = select_result.result
            logger.info(f"\n🔄 Executing: {next_task.id} - {next_task.action}")

            # Execute task
            executor_context = {
                "skill_registry": self.registry,
                "vault_path": str(self.vault_path),
                "groq_api_key": self.api_key,
                "groq_model": self.model
            }

            executor_input = SkillInput(
                data={"task": next_task},
                context=executor_context
            )

            exec_result = self.task_executor.execute(executor_input)

            # Update task in state
            for i, task in enumerate(state.tasks):
                if task.id == next_task.id:
                    state.tasks[i] = exec_result.result
                    break

            state.update_progress()
            tasks_executed += 1

            if exec_result.success:
                logger.info(f"✅ Task {next_task.id} completed")
            else:
                logger.warning(f"❌ Task {next_task.id} failed: {exec_result.error_message}")

        logger.info(f"\n📊 Executed {tasks_executed} tasks this iteration")
        logger.info(f"Progress: {state.tasks_completed}/{state.tasks_total} completed")

        return state

    def _evaluate_phase(self, state: ExecutionState, plan_path: Path) -> tuple[ExecutionState, Optional[EvaluationResult]]:
        """Evaluate execution progress"""
        logger.info("\n📈 PHASE: EVALUATION")
        state.phase = ExecutionPhase.EVALUATING

        # Read original plan for context
        plan_content = plan_path.read_text()

        evaluator_input = SkillInput(
            data={
                "execution_state": state,
                "original_plan": plan_content
            }
        )

        result = self.progress_evaluator.execute(evaluator_input)

        if not result.success:
            logger.warning(f"Evaluation failed: {result.error_message}")
            return state, None

        evaluation = result.result
        state.last_evaluation = evaluation

        logger.info(f"✅ Evaluation complete:")
        logger.info(f"  On Track: {'✅' if evaluation.on_track else '❌'} {evaluation.on_track}")
        logger.info(f"  Confidence: {evaluation.confidence}")
        logger.info(f"  Needs Adjustment: {evaluation.needs_adjustment}")
        logger.info(f"  Should Continue: {evaluation.should_continue}")

        if evaluation.blocking_issues:
            logger.info(f"  Blocking Issues: {evaluation.blocking_issues}")

        return state, evaluation

    def _adjust_phase(self, state: ExecutionState, evaluation: EvaluationResult, plan_path: Path) -> ExecutionState:
        """Adjust plan based on evaluation"""
        logger.info("\n🔧 PHASE: ADJUSTMENT")
        state.phase = ExecutionPhase.ADJUSTING

        plan_content = plan_path.read_text()

        adjuster_input = SkillInput(
            data={
                "execution_state": state,
                "evaluation": evaluation,
                "original_plan": plan_content
            }
        )

        result = self.plan_adjuster.execute(adjuster_input)

        if not result.success:
            logger.warning(f"Adjustment failed: {result.error_message}")
            return state

        state = result.result
        adjustments_count = result.metadata.get("adjustments_count", 0)

        logger.info(f"✅ Applied {adjustments_count} adjustments")

        return state

    def _finalize_execution(self, state: ExecutionState) -> ExecutionState:
        """Finalize execution and archive state"""
        logger.info("\n" + "="*60)
        logger.info("EXECUTION COMPLETE")
        logger.info("="*60)

        # Log summary
        logger.info(state.get_summary())

        # Save execution log
        self._save_execution_log(state)

        # Archive state
        archive_path = state.archive(self.vault_path)
        logger.info(f"📁 Execution archived: {archive_path}")

        return state

    def _save_execution_log(self, state: ExecutionState):
        """Save execution log as markdown"""
        logs_dir = self.vault_path / "Logs" / "execution_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / f"execution_{state.execution_id}.md"

        log_content = f"""{state.get_summary()}

## Detailed Task Results

"""

        for task in state.tasks:
            status_emoji = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.SKIPPED: "⏭️",
                TaskStatus.BLOCKED: "🚫",
                TaskStatus.PENDING: "📋"
            }.get(task.status, "❓")

            log_content += f"### {status_emoji} {task.id}: {task.action}\n\n"
            log_content += f"- **Skill:** {task.skill_name}\n"
            log_content += f"- **Status:** {task.status.value}\n"
            log_content += f"- **Priority:** {task.priority}\n"
            log_content += f"- **Attempts:** {task.attempts}/{task.max_attempts}\n"

            if task.dependencies:
                log_content += f"- **Dependencies:** {', '.join(task.dependencies)}\n"

            if task.error_message:
                log_content += f"- **Error:** {task.error_message}\n"

            log_content += "\n"

        log_file.write_text(log_content)
        logger.info(f"📝 Execution log saved: {log_file}")

    def _extract_goal(self, plan_content: str) -> str:
        """Extract goal from plan (same as TaskDecomposer)"""
        import re

        # Try YAML frontmatter first
        yaml_match = re.search(r'---\s*\n(.*?)\n---', plan_content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            goal_match = re.search(r'goal:\s*(.+)', yaml_content)
            if goal_match:
                return goal_match.group(1).strip()
            title_match = re.search(r'title:\s*(.+)', yaml_content)
            if title_match:
                return title_match.group(1).strip()

        # Fallback to first heading
        heading_match = re.search(r'^#\s+(.+)$', plan_content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        return "Execute Plan"


def main():
    """Main entry point for running the Groq execution agent"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Groq Execution Agent - FREE autonomous execution",
        epilog="Get your free API key at: https://console.groq.com/keys"
    )
    parser.add_argument(
        "--vault",
        default="/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault",
        help="Path to the AI employee vault"
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to Plan.md file to execute"
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        choices=[
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        help="Groq model to use (default: llama-3.3-70b-versatile)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Max iterations (default: 10)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume existing execution"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run agent
    try:
        agent = ExecutionAgent(
            vault_path=args.vault,
            model=args.model,
            max_iterations=args.max_iterations
        )

        plan_path = Path(args.plan)
        if not plan_path.exists():
            print(f"\n❌ Plan file not found: {plan_path}")
            sys.exit(1)

        state = agent.execute_plan(plan_path, resume=args.resume)

        if state.phase == ExecutionPhase.COMPLETED:
            print(f"\n✅ Execution completed successfully!")
            print(f"   Completed: {state.tasks_completed}/{state.tasks_total} tasks")
        else:
            print(f"\n⚠️ Execution ended with status: {state.phase.value}")
            print(f"   Completed: {state.tasks_completed}/{state.tasks_total} tasks")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Get your free GROQ_API_KEY at: https://console.groq.com/keys")
        print("Then add it to your .env file: GROQ_API_KEY=your_key_here")
        sys.exit(1)


if __name__ == "__main__":
    main()
