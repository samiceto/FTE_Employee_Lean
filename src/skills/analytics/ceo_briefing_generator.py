"""
CEOBriefingGenerator Skill - Integrate all data sources and generate comprehensive CEO briefing
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class CEOBriefingGenerator(BaseSkill):
    """
    Generate comprehensive weekly CEO briefing from aggregated data.

    Combines data from multiple sources:
    - Task completion data (WeeklyTaskCollector)
    - Financial data (AccountingAggregator)
    - Subscription audit (SubscriptionAuditor)
    - Bottleneck analysis (BottleneckAnalyzer)

    Uses Groq LLM for executive summary and recommendations.

    USES Groq API - Free.
    """

    SKILL_NAME = "ceo_briefing_generator"
    REQUIRES_LLM = True
    DESCRIPTION = "Generate comprehensive CEO briefing with executive summary"

    SYSTEM_PROMPT = """You are an executive business advisor creating weekly CEO briefings.

Your role is to synthesize business data and provide strategic insights in a concise, actionable format.

Guidelines:
- Be direct and business-focused
- Highlight both wins and concerns
- Provide specific, actionable recommendations
- Focus on trends and patterns, not just numbers
- Keep executive summary to 3-4 sentences maximum

Return ONLY valid JSON in this exact format:
{
    "executive_summary": "3-4 sentence summary highlighting key wins, concerns, and trends",
    "proactive_recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2"
    ],
    "trend_insights": [
        "Qualitative insight about trends in the data"
    ]
}"""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Generate CEO briefing from aggregated data.

        Args:
            input_data: SkillInput with data containing:
                - tasks_data: Dict from WeeklyTaskCollector (required)
                - accounting_data: Dict from AccountingAggregator (required)
                - subscription_audit: Dict from SubscriptionAuditor (required)
                - bottleneck_analysis: Dict from BottleneckAnalyzer (required)
                - week_start: ISO date string (required)
                - week_end: ISO date string (required)

        Returns:
            SkillOutput with briefing path and content

        Example:
            SkillInput(data={
                "tasks_data": {...},
                "accounting_data": {...},
                "subscription_audit": {...},
                "bottleneck_analysis": {...},
                "week_start": "2026-01-15",
                "week_end": "2026-01-21"
            })
        """
        # Validate input
        required_keys = ["tasks_data", "accounting_data", "subscription_audit",
                        "bottleneck_analysis", "week_start", "week_end"]
        error = self.validate_input(input_data, required_keys)
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            data = input_data.data
            week_start = datetime.fromisoformat(data["week_start"])
            week_end = datetime.fromisoformat(data["week_end"])

            # Generate LLM insights
            llm_insights = self._generate_llm_insights(data)

            # Build briefing content
            briefing_content = self._build_briefing(
                data,
                llm_insights,
                week_start,
                week_end
            )

            # Write briefing file
            briefing_path = self._write_briefing(briefing_content, week_end)

            # Create approval tasks for flagged subscriptions
            approval_tasks_created = self._create_approval_tasks(
                data["subscription_audit"].get("flagged_subscriptions", [])
            )

            # Extract key metrics for notification
            key_metrics = {
                "weekly_revenue": data["accounting_data"].get("weekly_revenue", 0),
                "weekly_net": data["accounting_data"].get("weekly_net", 0),
                "total_tasks": data["tasks_data"].get("total_tasks", 0),
                "efficiency_score": data["bottleneck_analysis"].get("efficiency_score", 0),
                "flagged_subscriptions": len(data["subscription_audit"].get("flagged_subscriptions", []))
            }

            # Extract action items
            action_items = []
            # Add subscription review items
            for sub in data["subscription_audit"].get("flagged_subscriptions", []):
                action_items.append(f"Review {sub['service']} subscription")

            # Add bottleneck recommendations
            for bottleneck in data["bottleneck_analysis"].get("bottlenecks", [])[:3]:
                action_items.append(bottleneck.get("recommendation", ""))

            logger.info(f"CEO briefing generated: {briefing_path}")

            return SkillOutput(
                result={
                    "briefing_path": str(briefing_path),
                    "briefing_content": briefing_content,
                    "key_metrics": key_metrics,
                    "action_items": action_items,
                    "approval_tasks_created": approval_tasks_created,
                    "date": week_end.strftime("%Y-%m-%d")
                },
                success=True,
                metadata={
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "briefing_length": len(briefing_content)
                }
            )

        except Exception as e:
            logger.error(f"CEOBriefingGenerator execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _generate_llm_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to generate executive summary and recommendations.

        Args:
            data: Aggregated data from all skills

        Returns:
            Dictionary with executive summary and recommendations
        """
        # Prepare data summary for LLM
        prompt = f"""Generate executive insights for this week's business data:

**Financial Performance:**
- Weekly Revenue: ${data['accounting_data'].get('weekly_revenue', 0):.2f}
- Weekly Expenses: ${data['accounting_data'].get('weekly_expenses', 0):.2f}
- Weekly Net: ${data['accounting_data'].get('weekly_net', 0):.2f}
- MTD Revenue: ${data['accounting_data'].get('mtd_revenue', 0):.2f}
- Revenue Target: ${data['accounting_data'].get('revenue_target', 0):.2f}
- Target Progress: {data['accounting_data'].get('target_progress', 0):.1f}%

**Task Completion:**
- Tasks Completed: {data['tasks_data'].get('total_tasks', 0)}
- Categories: {', '.join(data['tasks_data'].get('by_category', {}).keys())}

**Operational Efficiency:**
- Efficiency Score: {data['bottleneck_analysis'].get('efficiency_score', 0)}/100
- Bottlenecks Identified: {len(data['bottleneck_analysis'].get('bottlenecks', []))}

**Cost Optimization:**
- Total Subscription Cost: ${data['subscription_audit'].get('total_subscription_cost', 0):.2f}/month
- Flagged Subscriptions: {len(data['subscription_audit'].get('flagged_subscriptions', []))}
- Potential Savings: ${data['subscription_audit'].get('potential_monthly_savings', 0):.2f}/month

Provide:
1. Executive summary (3-4 sentences)
2. 2-3 proactive recommendations
3. Qualitative trend insights

Return ONLY valid JSON. No markdown, no explanations."""

        try:
            response = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.7,  # More creative for recommendations
                max_tokens=1500
            )

            # Parse JSON response
            insights = self._parse_json_response(response)

            if not insights:
                logger.warning("LLM JSON parsing failed, using fallback insights")
                insights = self._fallback_insights(data)

        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            insights = self._fallback_insights(data)

        # Validate structure
        if "executive_summary" not in insights:
            insights["executive_summary"] = "Weekly business audit completed successfully."
        if "proactive_recommendations" not in insights:
            insights["proactive_recommendations"] = []
        if "trend_insights" not in insights:
            insights["trend_insights"] = []

        return insights

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return None

    def _fallback_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic insights if LLM fails"""
        weekly_revenue = data['accounting_data'].get('weekly_revenue', 0)
        total_tasks = data['tasks_data'].get('total_tasks', 0)
        efficiency_score = data['bottleneck_analysis'].get('efficiency_score', 0)

        summary = f"This week saw ${weekly_revenue:.2f} in revenue with {total_tasks} tasks completed. "
        summary += f"Operational efficiency score: {efficiency_score}/100. "
        summary += f"{len(data['subscription_audit'].get('flagged_subscriptions', []))} subscriptions flagged for review."

        recommendations = [
            "Review weekly performance metrics and adjust priorities accordingly",
            "Address identified bottlenecks to improve operational efficiency"
        ]

        if data['subscription_audit'].get('flagged_subscriptions'):
            recommendations.append("Review flagged subscriptions for cost optimization opportunities")

        return {
            "executive_summary": summary,
            "proactive_recommendations": recommendations,
            "trend_insights": ["Weekly audit data available for trend analysis"]
        }

    def _build_briefing(self, data: Dict[str, Any], llm_insights: Dict[str, Any],
                       week_start: datetime, week_end: datetime) -> str:
        """Build comprehensive briefing markdown"""

        accounting = data["accounting_data"]
        tasks = data["tasks_data"]
        subscriptions = data["subscription_audit"]
        bottlenecks = data["bottleneck_analysis"]

        # Build markdown
        md = f"""# Weekly CEO Briefing - Week of {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}

## Executive Summary

{llm_insights.get('executive_summary', '')}

---

## Revenue & Financial Performance

### This Week
- **Revenue**: ${accounting.get('weekly_revenue', 0):,.2f}
- **Expenses**: ${accounting.get('weekly_expenses', 0):,.2f}
- **Net**: ${accounting.get('weekly_net', 0):,.2f}

### Month-to-Date
- **Revenue**: ${accounting.get('mtd_revenue', 0):,.2f}
- **Expenses**: ${accounting.get('mtd_expenses', 0):,.2f}
- **Net**: ${accounting.get('mtd_net', 0):,.2f}
- **Target**: ${accounting.get('revenue_target', 0):,.2f}
- **Progress**: {accounting.get('target_progress', 0):.1f}%

"""

        # Add expenses breakdown if available
        if accounting.get('expenses_by_category'):
            md += "\n### Expenses by Category\n"
            for category, amount in accounting.get('expenses_by_category', {}).items():
                md += f"- **{category}**: ${amount:,.2f}\n"

        # Task Completion
        md += f"""
---

## Task Completion Analysis

- **Tasks Completed**: {tasks.get('total_tasks', 0)}

### By Category
"""
        for category, count in tasks.get('by_category', {}).items():
            md += f"- **{category}**: {count} tasks\n"

        # Bottlenecks
        md += f"""
---

## Operational Efficiency

**Efficiency Score**: {bottlenecks.get('efficiency_score', 0)}/100

"""

        if bottlenecks.get('bottlenecks'):
            md += "### Bottlenecks Identified\n\n"
            for bottleneck in bottlenecks['bottlenecks']:
                md += f"#### {bottleneck.get('task_type', 'General')}\n"
                md += f"**Issue**: {bottleneck.get('issue', '')}\n\n"
                md += f"**Recommendation**: {bottleneck.get('recommendation', '')}\n\n"
        else:
            md += "No significant bottlenecks identified this week.\n\n"

        if bottlenecks.get('patterns'):
            md += "### Patterns Observed\n"
            for pattern in bottlenecks['patterns']:
                md += f"- {pattern}\n"

        # Subscriptions
        md += f"""
---

## Subscription Audit & Cost Optimization

- **Total Subscription Cost**: ${subscriptions.get('total_subscription_cost', 0):,.2f}/month
- **Potential Monthly Savings**: ${subscriptions.get('potential_monthly_savings', 0):,.2f}

"""

        if subscriptions.get('flagged_subscriptions'):
            md += "### Subscriptions Flagged for Review\n\n"
            md += "| Service | Cost/Month | Reasons | Recommendation |\n"
            md += "|---------|------------|---------|----------------|\n"
            for sub in subscriptions['flagged_subscriptions']:
                reasons = '; '.join(sub.get('reasons', []))
                md += f"| {sub['service']} | ${sub['cost']:.2f} | {reasons} | {sub.get('recommendation', '')} |\n"
            md += "\n**Note**: Approval tasks have been created in Pending_Approval/ for each flagged subscription.\n\n"
        else:
            md += "All subscriptions are healthy and actively used.\n\n"

        if subscriptions.get('healthy_subscriptions'):
            md += f"**Healthy Subscriptions**: {', '.join(subscriptions['healthy_subscriptions'])}\n\n"

        # Recommendations
        md += """
---

## Proactive Recommendations

"""
        for i, rec in enumerate(llm_insights.get('proactive_recommendations', []), 1):
            md += f"{i}. {rec}\n"

        # Trend Insights
        if llm_insights.get('trend_insights'):
            md += "\n### Trend Insights\n"
            for insight in llm_insights['trend_insights']:
                md += f"- {insight}\n"

        # Footer
        md += f"""
---

*Generated automatically on {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}*
*Next audit scheduled for: {self._calculate_next_audit(week_end).strftime('%A, %B %d, %Y at %I:%M %p')}*
"""

        return md

    def _write_briefing(self, content: str, week_end: datetime) -> Path:
        """Write briefing to file"""
        briefings_dir = Path(self.vault_path) / "Briefings"
        briefings_dir.mkdir(exist_ok=True)

        filename = f"Weekly_Briefing_{week_end.strftime('%Y-%m-%d')}.md"
        briefing_path = briefings_dir / filename

        briefing_path.write_text(content, encoding='utf-8')
        logger.info(f"Briefing written to {briefing_path}")

        return briefing_path

    def _create_approval_tasks(self, flagged_subscriptions: List[Dict[str, Any]]) -> int:
        """Create approval tasks for flagged subscriptions"""
        approval_dir = Path(self.vault_path) / "Pending_Approval"
        approval_dir.mkdir(exist_ok=True)

        created_count = 0

        for sub in flagged_subscriptions:
            service = sub['service']
            cost = sub['cost']
            reasons = '; '.join(sub.get('reasons', []))
            recommendation = sub.get('recommendation', '')

            task_content = f"""---
type: subscription_review
service: {service}
cost: ${cost:.2f}
created: {datetime.now().isoformat()}
priority: medium
---

# Review Subscription: {service}

## Details
- **Service**: {service}
- **Monthly Cost**: ${cost:.2f}
- **Potential Savings**: ${cost:.2f}/month (if cancelled)

## Reasons for Review
{reasons}

## Recommendation
{recommendation}

## Actions
- [ ] Review subscription usage and necessity
- [ ] Decide: Keep, Downgrade, or Cancel
- [ ] Update Current_Month.md with decision
- [ ] Move this file to Approved/ or Rejected/ when done
"""

            filename = f"SUB_REVIEW_{service.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
            task_path = approval_dir / filename

            # Don't overwrite if already exists
            if not task_path.exists():
                task_path.write_text(task_content, encoding='utf-8')
                created_count += 1

        logger.info(f"Created {created_count} approval tasks for subscriptions")
        return created_count

    def _calculate_next_audit(self, current_date: datetime) -> datetime:
        """Calculate next Sunday at 11 PM"""
        from datetime import timedelta

        # Find next Sunday
        days_until_sunday = (6 - current_date.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # Next week if today is Sunday

        next_sunday = current_date + timedelta(days=days_until_sunday)
        return next_sunday.replace(hour=23, minute=0, second=0, microsecond=0)
