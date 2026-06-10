"""
ExpenseTracker Skill - Parse and categorize expenses using Groq
"""
import logging
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class ExpenseTracker(BaseSkill):
    """
    Parse and categorize business expenses using Groq.

    This skill helps extract expense details from receipts or descriptions
    and categorize them properly for Odoo.

    USES Groq API - Free.
    """

    SKILL_NAME = "expense_tracker"
    REQUIRES_LLM = True
    DESCRIPTION = "Parse and categorize business expenses using Groq"

    SYSTEM_PROMPT = """You are an accounting assistant helping to categorize business expenses.
Parse the expense description and extract details.

Common expense categories:
- Office Expenses (supplies, equipment)
- Travel Expenses (airfare, hotels, meals)
- Marketing Expenses (advertising, promotions)
- Professional Services (legal, accounting, consulting)
- Utilities (internet, phone, electricity)
- Software Subscriptions
- Insurance
- Rent

Your response must be valid JSON:
{
    "description": "Clear expense description",
    "amount": number,
    "category": "Expense category",
    "vendor_name": "Vendor name if mentioned",
    "date": "YYYY-MM-DD if mentioned"
}"""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Parse and categorize expense.

        Args:
            input_data: SkillInput with data containing:
                - description: Expense description or receipt text (required)

        Returns:
            SkillOutput with structured expense data

        Example:
            SkillInput(data={
                "description": "Bought office supplies from Staples for $150.50"
            })

            Returns:
            {
                "description": "Office supplies",
                "amount": 150.50,
                "category": "Office Expenses",
                "vendor_name": "Staples"
            }
        """
        # Validate input
        error = self.validate_input(input_data, ["description"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            description = input_data.data["description"]

            # Build prompt
            prompt = f"""Parse this expense description:

"{description}"

Extract the expense details and categorize it appropriately.
Return ONLY valid JSON. No markdown, no explanations."""

            # Call Groq
            response = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.3
            )

            # Parse JSON from response
            expense_data = self._parse_json_response(response)

            if not expense_data:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Failed to parse expense data from LLM response"
                )

            logger.info(f"Categorized expense: {expense_data.get('category')} - ${expense_data.get('amount')}")

            return SkillOutput(
                result=expense_data,
                success=True,
                metadata={"description_length": len(description)}
            )

        except Exception as e:
            logger.error(f"ExpenseTracker execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response"""
        import re

        # Try to find JSON in code block
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return None
