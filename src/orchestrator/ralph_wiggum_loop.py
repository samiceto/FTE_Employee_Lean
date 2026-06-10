"""
Ralph Wiggum Loop Orchestrator - Autonomous execution loop
Mirrors ReasoningLoopOrchestrator structure for consistency

Periodically executes Plan.md files using ExecutionAgent.
Named after Ralph Wiggum from The Simpsons - autonomous and persistent!
"""
import os
import time
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.execution_agent import ExecutionAgent
from models.execution_state import ExecutionState, ExecutionPhase
from logging.audit_logger import audit_logger

load_dotenv()

logger = logging.getLogger(__name__)


class RalphWiggumLoop:
    """
    Orchestrator that runs the execution agent on a schedule.

    Features (mirrors ReasoningLoopOrchestrator):
    - Configurable interval (default: 5 minutes)
    - Finds and executes pending plans
    - Graceful shutdown handling
    - Dashboard updates
    - Automatic resume of interrupted executions
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 300,  # 5 minutes default
        model: str = "llama-3.3-70b-versatile",
        max_iterations: int = 10,
        max_tasks_per_iteration: int = 10
    ):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.model = model
        self.max_iterations = max_iterations
        self.max_tasks_per_iteration = max_tasks_per_iteration

        self.agent: Optional[ExecutionAgent] = None
        self.last_execution_time: Optional[datetime] = None
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _initialize_agent(self) -> bool:
        """Initialize the execution agent"""
        try:
            self.agent = ExecutionAgent(
                vault_path=str(self.vault_path),
                model=self.model,
                max_iterations=self.max_iterations,
                max_tasks_per_iteration=self.max_tasks_per_iteration
            )
            logger.info(f"Execution agent initialized with {self.model}")
            return True
        except ValueError as e:
            logger.error(f"Failed to initialize agent: {e}")
            logger.error("Make sure GROQ_API_KEY is set in your .env file")
            return False

    def _find_pending_plans(self) -> List[Path]:
        """Find Plan.md files that haven't been executed"""
        plans_dir = self.vault_path / "Plans"

        if not plans_dir.exists():
            return []

        # Get all plan files
        plan_files = list(plans_dir.glob("Plan_*.md"))

        # Check execution history to filter out already executed plans
        executed_plans = self._get_executed_plans()

        pending = [p for p in plan_files if p.name not in executed_plans]

        return sorted(pending, key=lambda p: p.stat().st_mtime)  # Oldest first

    def _get_executed_plans(self) -> set:
        """Get set of plan names that have been executed"""
        history_dir = self.vault_path / "ExecutionState" / "execution_history"

        if not history_dir.exists():
            return set()

        executed = set()

        # Check archived executions
        for archive_file in history_dir.glob("execution_*.json"):
            try:
                import json
                with open(archive_file, 'r') as f:
                    data = json.load(f)
                    plan_path = Path(data.get("plan_path", ""))
                    if plan_path.exists():
                        executed.add(plan_path.name)
            except Exception as e:
                logger.warning(f"Error reading archive {archive_file}: {e}")

        return executed

    def _should_resume(self) -> bool:
        """Check if there's an active execution to resume"""
        active_file = self.vault_path / "ExecutionState" / "active_execution.json"
        return active_file.exists()

    def _update_dashboard(self, state: Optional[ExecutionState]) -> None:
        """Update the dashboard with latest execution info"""
        dashboard_path = self.vault_path / "Dashboard.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if state:
            status_emoji = {
                ExecutionPhase.COMPLETED: "✅",
                ExecutionPhase.FAILED: "❌",
                ExecutionPhase.EXECUTING: "🔄",
            }.get(state.phase, "📋")

            status_line = f"- **Last Execution:** {status_emoji} {state.goal} - {state.tasks_completed}/{state.tasks_total} tasks at {timestamp}"
        else:
            status_line = f"- **Last Check:** {timestamp} (no plans to execute)"

        # Read current dashboard
        if dashboard_path.exists():
            content = dashboard_path.read_text()

            # Update or add execution status section
            if "## Ralph Wiggum Loop Status" in content:
                # Update existing section
                lines = content.split("\n")
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith("## Ralph Wiggum Loop Status"):
                        in_section = True
                        new_lines.append(line)
                        new_lines.append(status_line)
                    elif in_section and line.startswith("##"):
                        in_section = False
                        new_lines.append(line)
                    elif not in_section:
                        new_lines.append(line)
                content = "\n".join(new_lines)
            else:
                # Add new section
                content += f"\n\n## Ralph Wiggum Loop Status\n{status_line}\n"

            dashboard_path.write_text(content)
        else:
            # Create new dashboard
            dashboard_path.write_text(f"""# AI Employee Dashboard

## Ralph Wiggum Loop Status
{status_line}
""")

    def run_once(self) -> Optional[ExecutionState]:
        """Run the execution loop once"""
        if not self.agent and not self._initialize_agent():
            return None

        # Check for active execution to resume
        if self._should_resume():
            logger.info("Found active execution, resuming...")
            # Resume by executing with the existing state
            state = ExecutionState.load(self.vault_path)
            if state:
                plan_path = Path(state.plan_path)
                execution_id = f"{state.id}_{int(datetime.now().timestamp())}"

                # Log orchestrator start (resume)
                audit_logger.log_orchestrator_start(
                    orchestrator='ralph_wiggum_loop',
                    goal=state.goal,
                    execution_id=execution_id
                )

                start_time = time.time()
                state = self.agent.execute_plan(plan_path, resume=True)
                duration_ms = (time.time() - start_time) * 1000

                # Log orchestrator complete
                if state:
                    audit_logger.log_orchestrator_complete(
                        orchestrator='ralph_wiggum_loop',
                        execution_id=execution_id,
                        duration_ms=duration_ms,
                        tasks_completed=state.tasks_completed
                    )

                self._update_dashboard(state)
                return state

        # Find pending plans
        pending_plans = self._find_pending_plans()

        if not pending_plans:
            logger.info("No pending plans to execute")
            self._update_dashboard(None)
            return None

        # Execute first pending plan
        plan_path = pending_plans[0]
        logger.info(f"Executing plan: {plan_path.name}")

        # Generate execution ID
        execution_id = f"{plan_path.stem}_{int(datetime.now().timestamp())}"

        # Log orchestrator start
        # Load plan to get goal
        try:
            plan_content = plan_path.read_text()
            goal = plan_path.stem.replace('Plan_', '').replace('_', ' ')
        except Exception:
            goal = "unknown"

        audit_logger.log_orchestrator_start(
            orchestrator='ralph_wiggum_loop',
            goal=goal,
            execution_id=execution_id
        )

        start_time = time.time()
        state = self.agent.execute_plan(plan_path, resume=False)
        duration_ms = (time.time() - start_time) * 1000

        if state:
            self.last_execution_time = datetime.now()
            logger.info(f"✅ Execution completed: {state.goal}")

            # Log orchestrator complete
            audit_logger.log_orchestrator_complete(
                orchestrator='ralph_wiggum_loop',
                execution_id=execution_id,
                duration_ms=duration_ms,
                tasks_completed=state.tasks_completed
            )

        self._update_dashboard(state)
        return state

    def run_loop(self) -> None:
        """Run the execution loop continuously"""
        logger.info(f"Starting Ralph Wiggum Loop (interval: {self.check_interval}s)")
        logger.info(f"🤖 I'm helping! - Ralph Wiggum")

        if not self._initialize_agent():
            logger.error("Failed to initialize agent, exiting")
            return

        self.running = True

        while self.running:
            try:
                state = self.run_once()

                if state:
                    if state.phase == ExecutionPhase.COMPLETED:
                        logger.info(f"✅ Execution completed: {state.goal}")
                    else:
                        logger.warning(f"⚠️ Execution ended: {state.phase.value}")

            except Exception as e:
                logger.error(f"Error in Ralph Wiggum Loop: {e}", exc_info=True)
                audit_logger.log_error(
                    component='ralph_wiggum_loop',
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={'phase': 'run_loop'}
                )

            # Sleep in small intervals to allow graceful shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Ralph Wiggum Loop stopped")


def main():
    """Main entry point for the Ralph Wiggum Loop orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Loop - Autonomous execution orchestrator (FREE Groq-powered)",
        epilog="Named after Ralph Wiggum - autonomous and persistent! Get your free API key at: https://console.groq.com/keys"
    )
    parser.add_argument(
        "--vault",
        default="/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault",
        help="Path to the AI employee vault"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300 = 5 minutes)"
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
        help="Max iterations per execution (default: 10)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit"
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

    orchestrator = RalphWiggumLoop(
        vault_path=args.vault,
        check_interval=args.interval,
        model=args.model,
        max_iterations=args.max_iterations
    )

    if args.once:
        state = orchestrator.run_once()
        if state:
            if state.phase == ExecutionPhase.COMPLETED:
                print(f"\n✅ Execution completed: {state.goal}")
                print(f"   Tasks: {state.tasks_completed}/{state.tasks_total} completed")
            else:
                print(f"\n⚠️ Execution ended: {state.phase.value}")
                print(f"   Tasks: {state.tasks_completed}/{state.tasks_total} completed")
        else:
            print("\n📋 No executions performed (check logs for details)")
    else:
        print(f"🔄 Starting Ralph Wiggum Loop (interval: {args.interval}s)")
        print(f"   Model: {args.model}")
        print(f"   🤖 I'm helping! - Ralph Wiggum")
        print("   Press Ctrl+C to stop")
        orchestrator.run_loop()


if __name__ == "__main__":
    main()
