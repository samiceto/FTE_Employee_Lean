"""
Groq Reasoning Agent - Creates Plan.md files using Groq LLM
Refactored to use modular skill system for Silver Tier compliance
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Add parent directory to path for skills import
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills import get_registry, SkillInput

load_dotenv()

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """
    Groq-powered reasoning agent that analyzes tasks and creates Plan.md files.

    REFACTORED for Silver Tier compliance - uses modular skill system.
    Skills are auto-discovered and registered from the skills directory.

    Uses Groq's ultra-fast FREE inference with Llama 3.3 70B model.
    Get your free API key at: https://console.groq.com/keys
    """

    def __init__(
        self,
        vault_path: str,
        model: str = "llama-3.3-70b-versatile",
        api_key: Optional[str] = None
    ):
        self.vault_path = Path(vault_path)
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

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

        # Get skill instances
        self.task_analyzer = self.registry.get_skill("task_analyzer", **skill_kwargs)
        self.context_loader = self.registry.get_skill("context_loader", **skill_kwargs)
        self.plan_generator = self.registry.get_skill("plan_generator", **skill_kwargs)

        logger.info(f"Initialized reasoning agent with {self.model} and skill system")
        logger.info(f"Available skills: {list(self.registry.list_skills().keys())}")

    def collect_tasks(self, max_tasks: int = 20) -> list:
        """
        Collect pending tasks from Need_Action folder using TaskAnalyzer skill.

        Args:
            max_tasks: Maximum number of tasks to collect

        Returns:
            List of TaskItem objects
        """
        input_data = SkillInput(data={"max_tasks": max_tasks})
        result = self.task_analyzer.execute(input_data)

        if not result.success:
            logger.error(f"Task collection failed: {result.error_message}")
            return []

        logger.info(f"Collected {len(result.result)} tasks using TaskAnalyzer skill")
        return result.result

    def run_once(self, max_tasks: int = 20) -> Optional[Path]:
        """
        Run the reasoning loop once using skill system.

        This method orchestrates three skills:
        1. TaskAnalyzer - Collect tasks from Need_Action
        2. ContextLoader - Load business context
        3. PlanGenerator - Generate and save plan

        Args:
            max_tasks: Maximum number of tasks to process

        Returns:
            Path to generated plan, or None if no plan created
        """
        logger.info(f"Starting reasoning agent with skill system ({self.model})...")

        # Step 1: Collect tasks using TaskAnalyzer skill
        tasks = self.collect_tasks(max_tasks=max_tasks)
        logger.info(f"TaskAnalyzer collected {len(tasks)} tasks")

        if not tasks:
            logger.info("No tasks to process")
            return None

        # Step 2: Load business context using ContextLoader skill
        context_input = SkillInput(data={})
        context_result = self.context_loader.execute(context_input)

        if not context_result.success:
            logger.warning(f"Context loading failed: {context_result.error_message}")
            business_context = ""
        else:
            business_context = context_result.result
            logger.info(f"ContextLoader loaded {len(business_context)} chars of context")

        # Step 3: Generate plan using PlanGenerator skill
        plan_input = SkillInput(
            data={"tasks": tasks},
            context={"business_context": business_context}
        )
        plan_result = self.plan_generator.execute(plan_input)

        if not plan_result.success:
            logger.error(f"Plan generation failed: {plan_result.error_message}")
            return None

        plan_path = Path(plan_result.metadata.get("plan_path"))
        logger.info(f"PlanGenerator created plan: {plan_path}")

        return plan_path


def main():
    """Main entry point for running the Groq reasoning agent"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Groq Reasoning Agent - FREE ultra-fast inference",
        epilog="Get your free API key at: https://console.groq.com/keys"
    )
    parser.add_argument(
        "--vault",
        default="/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault",
        help="Path to the AI employee vault"
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
        "--max-tasks",
        type=int,
        default=15,
        help="Max tasks to process at once (default: 15)"
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
        agent = ReasoningAgent(
            vault_path=args.vault,
            model=args.model
        )
        plan_path = agent.run_once(max_tasks=args.max_tasks)

        if plan_path:
            print(f"\n✅ Plan created: {plan_path}")
        else:
            print("\n❌ No plan generated")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Get your free GROQ_API_KEY at: https://console.groq.com/keys")
        print("Then add it to your .env file: GROQ_API_KEY=your_key_here")


if __name__ == "__main__":
    main()
