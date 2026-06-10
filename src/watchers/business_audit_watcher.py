#!/usr/bin/env python3
"""
BusinessAuditWatcher - Schedule weekly business audits and orchestrate skill execution

Runs every Sunday at 11 PM to generate comprehensive CEO briefing.
"""
import argparse
import logging
import time
import signal
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Slack SDK for notifications
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("Slack SDK not available - notifications will be disabled")

from skills.analytics.weekly_task_collector import WeeklyTaskCollector
from skills.accounting.accounting_aggregator import AccountingAggregator
from skills.analytics.subscription_auditor import SubscriptionAuditor
from skills.analytics.bottleneck_analyzer import BottleneckAnalyzer
from skills.analytics.ceo_briefing_generator import CEOBriefingGenerator
from skills.base_skill import SkillInput
from core.retry_handler import with_retry
from core.errors import TransientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusinessAuditWatcher:
    """
    Autonomous weekly business audit system.

    Runs on schedule (default: Sunday 11 PM) to:
    1. Collect completed tasks from Done/ folder
    2. Aggregate financial data from accounting files
    3. Audit subscriptions for cost optimization
    4. Analyze bottlenecks using LLM
    5. Generate comprehensive CEO briefing
    6. Create approval tasks for flagged items
    7. Update Dashboard
    8. Send Slack notification (if configured)
    """

    def __init__(
        self,
        vault_path: str,
        audit_day: int = 6,  # Sunday (0=Monday, 6=Sunday)
        audit_hour: int = 23,  # 11 PM
        check_interval: int = 3600,  # Check every hour
        groq_api_key: Optional[str] = None,
        slack_channel: Optional[str] = None,
        slack_token: Optional[str] = None
    ):
        """
        Initialize the watcher.

        Args:
            vault_path: Path to AI employee vault
            audit_day: Day of week to run audit (0=Monday, 6=Sunday)
            audit_hour: Hour to run audit (0-23)
            check_interval: Seconds between checks
            groq_api_key: Optional Groq API key (reads from env if not provided)
            slack_channel: Optional Slack channel ID for notifications
            slack_token: Optional Slack bot token (reads from env if not provided)
        """
        self.vault_path = Path(vault_path)
        self.audit_day = audit_day
        self.audit_hour = audit_hour
        self.check_interval = check_interval

        # Ensure Briefings directory exists
        (self.vault_path / "Briefings").mkdir(exist_ok=True)

        # Initialize Slack client if configured
        self.slack_client = None
        self.slack_channel = slack_channel
        if SLACK_AVAILABLE and slack_channel:
            token = slack_token or os.getenv("SLACK_BOT_TOKEN")
            if token:
                try:
                    self.slack_client = WebClient(token=token)
                    logger.info(f"Slack notifications enabled for channel: {slack_channel}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Slack client: {e}")
            else:
                logger.warning("Slack channel specified but SLACK_BOT_TOKEN not found")

        # Initialize skills
        logger.info("Initializing skills...")
        self.task_collector = WeeklyTaskCollector(vault_path=str(self.vault_path))
        self.accounting_aggregator = AccountingAggregator(vault_path=str(self.vault_path))
        self.subscription_auditor = SubscriptionAuditor(vault_path=str(self.vault_path))
        self.bottleneck_analyzer = BottleneckAnalyzer(
            vault_path=str(self.vault_path),
            groq_api_key=groq_api_key
        )
        self.briefing_generator = CEOBriefingGenerator(
            vault_path=str(self.vault_path),
            groq_api_key=groq_api_key
        )

        self.running = True
        logger.info(f"BusinessAuditWatcher initialized - Schedule: {self._get_day_name(audit_day)} at {audit_hour}:00")

    def run(self):
        """Main loop - check schedule and run audits"""
        logger.info("Starting BusinessAuditWatcher...")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        while self.running:
            try:
                if self.should_run_audit():
                    logger.info("=== Starting Weekly Business Audit ===")
                    success = self.run_audit()

                    if success:
                        logger.info("=== Weekly Business Audit Completed Successfully ===")
                    else:
                        logger.error("=== Weekly Business Audit Failed ===")

                else:
                    next_audit = self._calculate_next_audit()
                    logger.debug(f"Not time for audit yet. Next audit: {next_audit.strftime('%A, %B %d at %I:%M %p')}")

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def should_run_audit(self) -> bool:
        """
        Check if it's time to run the audit.

        Returns:
            True if audit should run, False otherwise
        """
        now = datetime.now()

        # Check if it's the right day and hour
        if now.weekday() != self.audit_day or now.hour != self.audit_hour:
            return False

        # Check marker file to prevent duplicate runs
        marker_file = self.vault_path / "Briefings" / ".last_business_audit"

        if marker_file.exists():
            try:
                last_audit_str = marker_file.read_text().strip()
                last_audit = datetime.fromisoformat(last_audit_str)

                # Only run if it's been at least 6 days (allows for weekly schedule)
                if (now - last_audit).days < 6:
                    logger.debug(f"Audit already run recently: {last_audit.strftime('%Y-%m-%d %H:%M')}")
                    return False

            except Exception as e:
                logger.warning(f"Error reading marker file: {e}")

        return True

    def run_audit(self) -> bool:
        """
        Execute the full audit workflow.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate date range (previous 7 days)
            week_end = datetime.now()
            week_start = week_end - timedelta(days=7)

            logger.info(f"Audit period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")

            # 1. Collect tasks
            logger.info("Step 1/5: Collecting completed tasks...")
            tasks_result = self._execute_skill_with_retry(
                self.task_collector,
                SkillInput(data={
                    "start_date": week_start.date().isoformat(),
                    "end_date": week_end.date().isoformat()
                }),
                "WeeklyTaskCollector"
            )

            if not tasks_result:
                logger.error("Failed to collect tasks")
                return False

            logger.info(f"Collected {tasks_result.result['total_tasks']} tasks")

            # 2. Aggregate accounting data
            logger.info("Step 2/5: Aggregating financial data...")
            accounting_result = self._execute_skill_with_retry(
                self.accounting_aggregator,
                SkillInput(data={
                    "start_date": week_start.date().isoformat(),
                    "end_date": week_end.date().isoformat()
                }),
                "AccountingAggregator"
            )

            if not accounting_result:
                logger.error("Failed to aggregate accounting data")
                return False

            logger.info(f"Weekly revenue: ${accounting_result.result['weekly_revenue']:.2f}")

            # 3. Audit subscriptions
            logger.info("Step 3/5: Auditing subscriptions...")
            audit_rules = self._load_audit_rules()
            subscription_result = self._execute_skill_with_retry(
                self.subscription_auditor,
                SkillInput(data={
                    "subscriptions": accounting_result.result.get("subscriptions", []),
                    "audit_rules": audit_rules
                }),
                "SubscriptionAuditor"
            )

            if not subscription_result:
                logger.error("Failed to audit subscriptions")
                return False

            logger.info(f"Flagged {len(subscription_result.result['flagged_subscriptions'])} subscriptions")

            # 4. Analyze bottlenecks
            logger.info("Step 4/5: Analyzing bottlenecks...")
            bottleneck_result = self._execute_skill_with_retry(
                self.bottleneck_analyzer,
                SkillInput(data={
                    "tasks": tasks_result.result.get("tasks", [])
                }),
                "BottleneckAnalyzer"
            )

            if not bottleneck_result:
                logger.error("Failed to analyze bottlenecks")
                return False

            logger.info(f"Efficiency score: {bottleneck_result.result['efficiency_score']}/100")

            # 5. Generate briefing
            logger.info("Step 5/5: Generating CEO briefing...")
            briefing_result = self._execute_skill_with_retry(
                self.briefing_generator,
                SkillInput(data={
                    "tasks_data": tasks_result.result,
                    "accounting_data": accounting_result.result,
                    "subscription_audit": subscription_result.result,
                    "bottleneck_analysis": bottleneck_result.result,
                    "week_start": week_start.date().isoformat(),
                    "week_end": week_end.date().isoformat()
                }),
                "CEOBriefingGenerator"
            )

            if not briefing_result:
                logger.error("Failed to generate briefing")
                return False

            logger.info(f"Briefing created: {briefing_result.result['briefing_path']}")
            logger.info(f"Approval tasks created: {briefing_result.result['approval_tasks_created']}")

            # 6. Update marker file
            self._update_marker_file()

            # 7. Update Dashboard
            self._update_dashboard(briefing_result.result)

            # 8. Send Slack notification (if configured)
            self._send_slack_notification(briefing_result.result)

            return True

        except Exception as e:
            logger.error(f"Audit execution failed: {e}", exc_info=True)
            return False

    def _execute_skill_with_retry(self, skill, input_data: SkillInput, skill_name: str, max_retries: int = 3):
        """
        Execute skill with retry logic using @with_retry decorator.

        Args:
            skill: Skill instance
            input_data: SkillInput
            skill_name: Name for logging
            max_retries: Maximum retry attempts

        Returns:
            SkillOutput or None if all retries fail
        """
        @with_retry(max_attempts=max_retries, base_delay=1, max_delay=60)
        def _execute():
            result = skill.execute(input_data)

            # If skill execution failed, raise TransientError to trigger retry
            if not result.success:
                raise TransientError(f"{skill_name} failed: {result.error_message}")

            return result

        try:
            return _execute()
        except TransientError as e:
            logger.error(f"{skill_name} failed after {max_retries} attempts: {e}")
            return None
        except Exception as e:
            logger.error(f"{skill_name} unexpected error: {e}", exc_info=True)
            return None

    def _load_audit_rules(self) -> Dict[str, Any]:
        """Load subscription audit rules from Business_Goals.md"""
        rules = {}

        try:
            goals_path = self.vault_path / "Business_Goals.md"
            if goals_path.exists():
                content = goals_path.read_text(encoding='utf-8')

                # Parse audit rules section
                # This is a simple implementation - could be enhanced
                if "inactivity_days" in content.lower():
                    # Extract values if present
                    pass

        except Exception as e:
            logger.warning(f"Error loading audit rules: {e}")

        return rules

    def _update_marker_file(self):
        """Update marker file with current timestamp"""
        try:
            marker_file = self.vault_path / "Briefings" / ".last_business_audit"
            marker_file.write_text(datetime.now().isoformat(), encoding='utf-8')
            logger.info("Marker file updated")

        except Exception as e:
            logger.error(f"Failed to update marker file: {e}")

    def _update_dashboard(self, briefing_data: Dict[str, Any]):
        """Update Dashboard.md with audit status"""
        try:
            dashboard_path = self.vault_path / "Dashboard.md"

            # Read existing dashboard
            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding='utf-8')
            else:
                content = "# Dashboard\n\n"

            # Prepare audit status section
            next_audit = self._calculate_next_audit()
            audit_section = f"""
## Business Audit Status

- **Last Audit**: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}
- **Next Audit**: {next_audit.strftime('%A, %B %d, %Y at %I:%M %p')}
- **Latest Briefing**: [Weekly_Briefing_{briefing_data['date']}.md](Briefings/Weekly_Briefing_{briefing_data['date']}.md)
- **Action Items**: {len(briefing_data['action_items'])} pending review
- **Key Metrics**:
  - Revenue: ${briefing_data['key_metrics']['weekly_revenue']:.2f}
  - Tasks Completed: {briefing_data['key_metrics']['total_tasks']}
  - Efficiency Score: {briefing_data['key_metrics']['efficiency_score']}/100
"""

            # Replace or append audit section
            if "## Business Audit Status" in content:
                # Replace existing section
                import re
                pattern = r"## Business Audit Status.*?(?=\n## |\Z)"
                content = re.sub(pattern, audit_section.strip(), content, flags=re.DOTALL)
            else:
                # Append new section
                content += "\n" + audit_section

            # Write updated dashboard
            dashboard_path.write_text(content, encoding='utf-8')
            logger.info("Dashboard updated")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def _send_slack_notification(self, briefing_data: Dict[str, Any]):
        """Send briefing summary to Slack (if configured)"""
        if not self.slack_client or not self.slack_channel:
            logger.debug("Slack not configured - skipping notification")
            return

        try:
            # Build Slack message with formatting
            slack_message = f"""📊 *Weekly CEO Briefing Available*
Week ending {briefing_data['date']}

*Key Metrics:*
• Revenue: ${briefing_data['key_metrics']['weekly_revenue']:.2f}
• Tasks Completed: {briefing_data['key_metrics']['total_tasks']}
• Efficiency Score: {briefing_data['key_metrics']['efficiency_score']}/100
• Action Items: {len(briefing_data['action_items'])}

*View full briefing:* `Briefings/Weekly_Briefing_{briefing_data['date']}.md`
"""

            # Send to Slack
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=slack_message,
                unfurl_links=False,
                unfurl_media=False
            )

            if response["ok"]:
                logger.info(f"Slack notification sent successfully to {self.slack_channel}")
            else:
                logger.warning(f"Slack notification failed: {response}")

        except SlackApiError as e:
            logger.warning(f"Slack API error: {e.response['error']}")
        except Exception as e:
            logger.warning(f"Failed to send Slack notification: {e}")

    def _calculate_next_audit(self) -> datetime:
        """Calculate next scheduled audit time"""
        now = datetime.now()

        # Calculate days until target day
        days_until_target = (self.audit_day - now.weekday()) % 7
        if days_until_target == 0 and now.hour >= self.audit_hour:
            days_until_target = 7  # Next week

        next_audit = now + timedelta(days=days_until_target)
        next_audit = next_audit.replace(hour=self.audit_hour, minute=0, second=0, microsecond=0)

        return next_audit

    def _get_day_name(self, day_num: int) -> str:
        """Get day name from number"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[day_num]

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Weekly Business Audit Watcher")
    parser.add_argument("--vault", required=True, help="Path to AI employee vault")
    parser.add_argument("--day", type=int, default=6, help="Day of week for audit (0=Monday, 6=Sunday)")
    parser.add_argument("--hour", type=int, default=23, help="Hour for audit (0-23)")
    parser.add_argument("--interval", type=int, default=3600, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run audit once and exit (for testing)")
    parser.add_argument("--groq-api-key", help="Groq API key (optional, reads from env if not provided)")
    parser.add_argument("--slack-channel", help="Slack channel ID for notifications (optional)")
    parser.add_argument("--slack-token", help="Slack bot token (optional, reads from env if not provided)")

    args = parser.parse_args()

    # Create watcher
    watcher = BusinessAuditWatcher(
        vault_path=args.vault,
        audit_day=args.day,
        audit_hour=args.hour,
        check_interval=args.interval,
        groq_api_key=args.groq_api_key,
        slack_channel=args.slack_channel,
        slack_token=args.slack_token
    )

    if args.once:
        # Run once and exit (for testing)
        logger.info("Running audit once (--once mode)...")
        success = watcher.run_audit()
        sys.exit(0 if success else 1)
    else:
        # Run continuously
        watcher.run()


if __name__ == "__main__":
    main()
