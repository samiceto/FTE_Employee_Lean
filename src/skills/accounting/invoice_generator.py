"""
InvoiceGenerator Skill - Use Groq to help generate invoices from descriptions
"""
import logging
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class InvoiceGenerator(BaseSkill):
    """
    Generate invoice data from natural language descriptions using Groq.

    This skill helps create structured invoice data from unstructured input,
    making it easier to create invoices in Odoo.

    USES Groq API - Free.
    """

    SKILL_NAME = "invoice_generator"
    REQUIRES_LLM = True
    DESCRIPTION = "Generate structured invoice data from natural language using Groq"

    SYSTEM_PROMPT = """You are an accounting assistant helping to create invoices.
Parse the user's description and extract invoice details.

Your response must be valid JSON with this structure:
{
    "partner_name": "Customer name",
    "invoice_lines": [
        {
            "product": "Product/Service name",
            "quantity": number,
            "price": number
        }
    ],
    "notes": "Any additional notes or observations"
}

Be precise with numbers and names."""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Generate invoice data from description.

        Args:
            input_data: SkillInput with data containing:
                - description: Natural language invoice description (required)

        Returns:
            SkillOutput with structured invoice data

        Example:
            SkillInput(data={
                "description": "Invoice ABC Corp for 10 hours of consulting at $150/hour and 5 hours of development at $200/hour"
            })

            Returns:
            {
                "partner_name": "ABC Corp",
                "invoice_lines": [
                    {"product": "Consulting", "quantity": 10, "price": 150.0},
                    {"product": "Development", "quantity": 5, "price": 200.0}
                ]
            }
        """
        # Validate input
        error = self.validate_input(input_data, ["description"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            description = input_data.data["description"]

            # Build prompt
            prompt = f"""Parse this invoice description and extract the details:

"{description}"

Return ONLY valid JSON with the invoice structure. No markdown, no explanations."""

            # Call Groq
            response = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.3  # Lower temperature for accuracy
            )

            # Parse JSON from response
            invoice_data = self._parse_json_response(response)

            if not invoice_data:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message="Failed to parse invoice data from LLM response"
                )

            logger.info(f"Generated invoice for {invoice_data.get('partner_name')}")

            return SkillOutput(
                result=invoice_data,
                success=True,
                metadata={"description_length": len(description)}
            )

        except Exception as e:
            logger.error(f"InvoiceGenerator execution failed: {e}")
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
