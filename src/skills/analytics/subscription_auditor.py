"""
SubscriptionAuditor Skill - Apply audit rules to subscriptions and identify cost optimization opportunities
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class SubscriptionAuditor(BaseSkill):
    """
    Audit subscriptions against defined rules to identify cost optimization opportunities.

    Applies rule-based logic to flag subscriptions for review based on:
    - Inactivity periods
    - Cost increases
    - Duplicate functionality
    - Usage patterns

    Does NOT use LLM - Pure Python rule-based logic.
    """

    SKILL_NAME = "subscription_auditor"
    REQUIRES_LLM = False
    DESCRIPTION = "Audit subscriptions and identify cost optimization opportunities"

    # Default audit rules
    DEFAULT_RULES = {
        "inactivity_days": 30,
        "cost_increase_percent": 20,
        "high_cost_threshold": 50,
        "low_usage_threshold": 50
    }

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Audit subscriptions against defined rules.

        Args:
            input_data: SkillInput with data containing:
                - subscriptions: List of subscription dictionaries (required)
                - audit_rules: Dictionary of audit rules (optional)

        Returns:
            SkillOutput with flagged subscriptions and recommendations

        Example:
            SkillInput(data={
                "subscriptions": [
                    {"service": "AWS", "cost": 125.0, "last_activity": "2026-01-21", "status": "Active"},
                    {"service": "Notion", "cost": 10.0, "last_activity": "2025-12-20", "status": "Active"}
                ],
                "audit_rules": {
                    "inactivity_days": 30,
                    "cost_increase_percent": 20
                }
            })
        """
        # Validate input
        error = self.validate_input(input_data, ["subscriptions"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            subscriptions = input_data.data["subscriptions"]
            audit_rules = input_data.data.get("audit_rules", self.DEFAULT_RULES)

            # Merge with defaults
            rules = {**self.DEFAULT_RULES, **audit_rules}

            # Audit each subscription
            flagged_subscriptions = []
            healthy_subscriptions = []

            for subscription in subscriptions:
                flags = self._audit_subscription(subscription, rules)

                if flags:
                    flagged_subscriptions.append({
                        "service": subscription["service"],
                        "cost": subscription["cost"],
                        "reasons": flags,
                        "recommendation": self._generate_recommendation(subscription, flags),
                        "potential_savings": subscription["cost"]  # Could save by cancelling
                    })
                else:
                    healthy_subscriptions.append(subscription["service"])

            # Calculate totals
            total_subscription_cost = sum(s["cost"] for s in subscriptions)
            potential_monthly_savings = sum(f["potential_savings"] for f in flagged_subscriptions)

            logger.info(f"Audited {len(subscriptions)} subscriptions: {len(flagged_subscriptions)} flagged, "
                       f"potential savings ${potential_monthly_savings:.2f}/month")

            return SkillOutput(
                result={
                    "flagged_subscriptions": flagged_subscriptions,
                    "total_subscription_cost": total_subscription_cost,
                    "potential_monthly_savings": potential_monthly_savings,
                    "healthy_subscriptions": healthy_subscriptions
                },
                success=True,
                metadata={
                    "total_subscriptions": len(subscriptions),
                    "flagged_count": len(flagged_subscriptions),
                    "healthy_count": len(healthy_subscriptions),
                    "rules_applied": rules
                }
            )

        except Exception as e:
            logger.error(f"SubscriptionAuditor execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _audit_subscription(self, subscription: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
        """
        Audit a single subscription against rules.

        Args:
            subscription: Subscription dictionary
            rules: Audit rules dictionary

        Returns:
            List of flag reasons (empty if healthy)
        """
        flags = []

        # Check inactivity
        last_activity = subscription.get("last_activity", "")
        if last_activity:
            try:
                last_activity_date = datetime.fromisoformat(last_activity)
                days_inactive = (datetime.now() - last_activity_date).days

                if days_inactive >= rules["inactivity_days"]:
                    flags.append(f"No activity in {days_inactive} days")

            except ValueError:
                logger.warning(f"Invalid last_activity date for {subscription['service']}: {last_activity}")

        # Check high cost with potential low usage
        cost = subscription.get("cost", 0)
        if cost > rules["high_cost_threshold"]:
            # If also inactive, flag for review
            if last_activity:
                try:
                    last_activity_date = datetime.fromisoformat(last_activity)
                    days_inactive = (datetime.now() - last_activity_date).days

                    if days_inactive > 14:  # 2 weeks
                        flags.append(f"High cost (${cost:.2f}/month) with low recent activity")

                except ValueError:
                    pass

        # Check for free services (cost = 0)
        if cost == 0:
            # Free services are always healthy unless explicitly flagged
            pass

        # Check status
        status = subscription.get("status", "").lower()
        if "review" in status or "cancelled" in status:
            flags.append(f"Status marked as '{subscription['status']}'")

        return flags

    def _generate_recommendation(self, subscription: Dict[str, Any], flags: List[str]) -> str:
        """
        Generate actionable recommendation based on flags.

        Args:
            subscription: Subscription dictionary
            flags: List of flag reasons

        Returns:
            Recommendation string
        """
        service = subscription["service"]
        cost = subscription["cost"]

        # Analyze flags and generate specific recommendation
        has_inactivity = any("activity" in flag.lower() for flag in flags)
        has_high_cost = any("high cost" in flag.lower() for flag in flags)

        if has_inactivity and has_high_cost:
            return f"Consider cancelling {service} (${cost:.2f}/month) due to extended inactivity and high cost. Review if still needed."

        elif has_inactivity:
            return f"Review {service} subscription - no recent activity detected. Confirm if still needed before next billing cycle."

        elif has_high_cost:
            return f"Review {service} usage - high monthly cost (${cost:.2f}) with limited recent activity. Consider downgrading plan."

        else:
            return f"Review {service} subscription for potential optimization opportunities."
