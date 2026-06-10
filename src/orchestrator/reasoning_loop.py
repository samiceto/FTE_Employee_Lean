"""
Reasoning Loop Orchestrator - Periodically runs Groq reasoning agent
to analyze pending tasks and generate Plan.md files.

REFACTORED for Silver Tier compliance - uses skill-based reasoning agent.
"""
import os
import time
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.reasoning_agent import ReasoningAgent

load_dotenv()

logger = logging.getLogger(__name__)


class ReasoningLoopOrchestrator:
    """
    Orchestrator that runs the reasoning agent on a schedule.

    Features:
    - Configurable interval (default: 30 minutes)
    - Minimum task threshold before running
    - Cooldown period after plan generation
    - Graceful shutdown handling
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 1800,  # 30 minutes default
        min_tasks: int = 1,
        cooldown_minutes: int = 60,
        model: str = "llama-3.3-70b-versatile",
        max_tasks: int = 15
    ):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.min_tasks = min_tasks
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.model = model
        self.max_tasks = max_tasks

        self.agent: Optional[ReasoningAgent] = None
        self.last_plan_time: Optional[datetime] = None
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _initialize_agent(self) -> bool:
        """Initialize the Groq reasoning agent"""
        try:
            self.agent = ReasoningAgent(
                vault_path=str(self.vault_path),
                model=self.model
            )
            logger.info(f"Groq reasoning agent initialized with {self.model}")
            return True
        except ValueError as e:
            logger.error(f"Failed to initialize agent: {e}")
            logger.error("Make sure GROQ_API_KEY is set in your .env file")
            return False

    def _should_run(self) -> tuple[bool, str]:
        """
        Determine if the reasoning loop should run.
        Returns (should_run, reason)
        """
        if not self.agent:
            return False, "Agent not initialized"

        # Check cooldown
        if self.last_plan_time:
            time_since_last = datetime.now() - self.last_plan_time
            if time_since_last < self.cooldown:
                remaining = self.cooldown - time_since_last
                return False, f"Cooldown active ({remaining.seconds // 60}m remaining)"

        # Check task count
        tasks = self.agent.collect_tasks()
        if len(tasks) < self.min_tasks:
            return False, f"Not enough tasks ({len(tasks)} < {self.min_tasks})"

        return True, f"Ready to process {len(tasks)} tasks"

    def _update_dashboard(self, plan_path: Optional[Path]) -> None:
        """Update the dashboard with latest plan info"""
        dashboard_path = self.vault_path / "Dashboard.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if plan_path:
            status_line = f"- **Last Plan:** [{plan_path.name}](Plans/{plan_path.name}) at {timestamp}"
        else:
            status_line = f"- **Last Check:** {timestamp} (no plan needed)"

        # Read current dashboard
        if dashboard_path.exists():
            content = dashboard_path.read_text()

            # Update or add reasoning status section
            if "## Reasoning Agent Status" in content:
                # Update existing section
                lines = content.split("\n")
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith("## Reasoning Agent Status"):
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
                content += f"\n\n## Reasoning Agent Status\n{status_line}\n"

            dashboard_path.write_text(content)
        else:
            # Create new dashboard
            dashboard_path.write_text(f"""# AI Employee Dashboard

## Reasoning Agent Status
{status_line}
""")

    def run_once(self) -> Optional[Path]:
        """Run the reasoning loop once"""
        if not self.agent and not self._initialize_agent():
            return None

        should_run, reason = self._should_run()
        logger.info(f"Run check: {reason}")

        if not should_run:
            return None

        logger.info("Running reasoning agent...")
        plan_path = self.agent.run_once()

        if plan_path:
            self.last_plan_time = datetime.now()
            logger.info(f"Plan generated: {plan_path}")

        self._update_dashboard(plan_path)
        return plan_path

    def run_loop(self) -> None:
        """Run the reasoning loop continuously"""
        logger.info(f"Starting reasoning loop (interval: {self.check_interval}s)")

        if not self._initialize_agent():
            logger.error("Failed to initialize agent, exiting")
            return

        self.running = True

        while self.running:
            try:
                plan_path = self.run_once()

                if plan_path:
                    logger.info(f"✅ Plan created: {plan_path.name}")

            except Exception as e:
                logger.error(f"Error in reasoning loop: {e}", exc_info=True)

            # Sleep in small intervals to allow graceful shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Reasoning loop stopped")


def main():
    """Main entry point for the Groq reasoning loop orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Groq Reasoning Loop Orchestrator - FREE ultra-fast AI planning",
        epilog="Get your free API key at: https://console.groq.com/keys"
    )
    parser.add_argument(
        "--vault",
        default="/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault",
        help="Path to the AI employee vault"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="Check interval in seconds (default: 1800 = 30 minutes)"
    )
    parser.add_argument(
        "--min-tasks",
        type=int,
        default=1,
        help="Minimum number of tasks before running (default: 1)"
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=60,
        help="Cooldown in minutes after generating a plan (default: 60)"
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

    orchestrator = ReasoningLoopOrchestrator(
        vault_path=args.vault,
        check_interval=args.interval,
        min_tasks=args.min_tasks,
        cooldown_minutes=args.cooldown,
        model=args.model
    )

    if args.once:
        plan_path = orchestrator.run_once()
        if plan_path:
            print(f"\n✅ Plan created: {plan_path}")
        else:
            print("\n📋 No plan generated (check logs for details)")
    else:
        print(f"🔄 Starting Groq reasoning loop (interval: {args.interval}s)")
        print(f"   Model: {args.model}")
        print("   Press Ctrl+C to stop")
        orchestrator.run_loop()


if __name__ == "__main__":
    main()
