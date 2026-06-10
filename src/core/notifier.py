"""
Alert and notification system for error recovery.

Provides multi-channel alerting (Slack, Dashboard, Email) with rate limiting
to prevent alert fatigue.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertLevel:
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Notifier:
    """Alert system for errors and system events"""

    def __init__(self):
        """Initialize notifier with configuration from environment"""
        # Slack configuration
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL_ID')
        self.slack_client = None

        if self.slack_token:
            try:
                from slack_sdk import WebClient
                self.slack_client = WebClient(token=self.slack_token)
                logger.info(f"Slack notifications enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack client: {e}")

        # Dashboard configuration
        self.vault_path = Path(os.getenv(
            'VAULT_PATH',
            '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'
        ))
        self.dashboard_path = self.vault_path / 'Dashboard.md'

        # Rate limiting: max 1 alert per component per 5 minutes
        self.alert_history = {}  # {component: last_alert_time}
        self.rate_limit_seconds = 300

    def can_alert(self, component: str) -> bool:
        """
        Check if component can send alert (rate limiting).

        Args:
            component: Component name

        Returns:
            True if alert is allowed
        """
        now = datetime.now()

        if component in self.alert_history:
            last_alert = self.alert_history[component]
            if (now - last_alert).total_seconds() < self.rate_limit_seconds:
                return False

        return True

    def alert(self, level: str, component: str, message: str):
        """
        Send alert through all channels.

        Args:
            level: Alert level (INFO, WARNING, CRITICAL)
            component: Component name
            message: Alert message
        """
        if not self.can_alert(component):
            logger.debug(f"Alert for {component} rate-limited, skipping")
            return

        self.alert_history[component] = datetime.now()

        # Log
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        log_method(f"[{level}] {component}: {message}")

        # Slack (for WARNING and CRITICAL only)
        if self.slack_client and level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self._send_slack(level, component, message)

        # Dashboard (all levels)
        self._update_dashboard(level, component, message)

        # Email (fallback for CRITICAL if Slack unavailable)
        if level == AlertLevel.CRITICAL and not self.slack_client:
            self._send_email_alert(component, message)

    def _send_slack(self, level: str, component: str, message: str):
        """
        Send Slack notification.

        Args:
            level: Alert level
            component: Component name
            message: Alert message
        """
        try:
            emoji = {
                AlertLevel.INFO: ":information_source:",
                AlertLevel.WARNING: ":warning:",
                AlertLevel.CRITICAL: ":rotating_light:"
            }.get(level, ":bell:")

            self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=f"{emoji} *{level}*: {component}\n{message}"
            )
            logger.info(f"Slack alert sent for {component}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _update_dashboard(self, level: str, component: str, message: str):
        """
        Update Dashboard.md with alert.

        Args:
            level: Alert level
            component: Component name
            message: Alert message
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_line = f"- **[{timestamp}]** [{level}] {component}: {message}\n"

            # Ensure dashboard file exists
            if not self.dashboard_path.exists():
                self.dashboard_path.parent.mkdir(parents=True, exist_ok=True)
                self.dashboard_path.write_text("# Dashboard\n\n## Recent Alerts\n\n")

            content = self.dashboard_path.read_text()

            # Add to alerts section
            if "## Recent Alerts" in content:
                parts = content.split("## Recent Alerts")
                # Insert at beginning of alerts section
                content = parts[0] + "## Recent Alerts\n\n" + alert_line
                if len(parts) > 1:
                    content += parts[1].lstrip()
            else:
                content += f"\n\n## Recent Alerts\n\n{alert_line}"

            self.dashboard_path.write_text(content)
            logger.debug(f"Dashboard updated with {level} alert for {component}")
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def _send_email_alert(self, component: str, message: str):
        """
        Send email alert (fallback for critical issues).

        Args:
            component: Component name
            message: Alert message
        """
        try:
            # Import here to avoid circular dependency
            import asyncio
            from src.mcp_servers.email.mcp_server_email import send_email

            admin_email = os.getenv('ADMIN_EMAIL')
            if not admin_email:
                logger.warning("ADMIN_EMAIL not set, cannot send email alert")
                return

            # Run async send_email in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(send_email(
                    receiver=[admin_email],
                    subject=f"CRITICAL: {component} Failure",
                    body=f"Critical failure in {component}:\n\n{message}",
                    attachments=[],
                    attachment_dir=None
                ))
                logger.info(f"Email alert sent for {component}")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
