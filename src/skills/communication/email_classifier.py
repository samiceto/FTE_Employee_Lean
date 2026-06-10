"""
EmailClassifier Skill - Classifies emails by urgency and type using Groq LLM
NEW skill for Silver Tier compliance
"""
import logging
import json
from typing import Optional

from ..base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class EmailClassifier(BaseSkill):
    """
    Classifies emails by urgency, type, and suggests actions.

    This skill uses Groq LLM to analyze email content and:
    - Classify urgency (urgent, high, normal, low, spam)
    - Identify email type (inquiry, invoice, support, newsletter, etc.)
    - Extract key entities (client names, deadlines, amounts)
    - Suggest appropriate actions

    USES Groq API - Free but requires API key.
    """

    SKILL_NAME = "email_classifier"
    REQUIRES_LLM = True
    DESCRIPTION = "Classify and analyze emails using Groq LLM"

    SYSTEM_PROMPT = """You are an email classification and triage assistant.
Your role is to analyze emails and classify them for prioritization.

Classification Categories:
1. **Urgency Levels:**
   - urgent: Requires immediate attention (deadlines, emergencies, angry clients)
   - high: Important but not immediate (new inquiries, project updates)
   - normal: Regular business emails
   - low: Informational, can wait
   - spam: Promotional, newsletters, irrelevant

2. **Email Types:**
   - inquiry: New client or project inquiry
   - invoice: Payment-related (invoices, receipts, payment requests)
   - support: Technical support or help requests
   - meeting: Meeting requests or scheduling
   - update: Project status updates
   - newsletter: Marketing or informational emails
   - personal: Personal communications

3. **Key Entities to Extract:**
   - Client/sender names
   - Deadlines or dates mentioned
   - Monetary amounts
   - Action items

Provide structured, actionable classification that helps prioritize inbox."""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Classify an email.

        Args:
            input_data: SkillInput with data containing:
                - subject: Email subject line (required)
                - body: Email body text (required)
                - sender: Sender email address (optional)

        Returns:
            SkillOutput with classification results
        """
        # Validate input
        error = self.validate_input(input_data, ["subject", "body"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            subject = input_data.data["subject"]
            body = input_data.data["body"]
            sender = input_data.data.get("sender", "Unknown")

            # Build classification prompt
            prompt = self._build_classification_prompt(subject, body, sender)

            # Call Groq
            response = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=1500
            )

            # Parse response
            result = self._parse_classification_response(response)

            return SkillOutput(
                result=result,
                success=True,
                metadata={
                    "sender": sender,
                    "subject_length": len(subject),
                    "body_length": len(body)
                }
            )

        except Exception as e:
            logger.error(f"EmailClassifier execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _build_classification_prompt(self, subject: str, body: str, sender: str) -> str:
        """Build the prompt for email classification"""
        # Truncate body if too long (keep first 1000 chars)
        body_preview = body[:1000] + ("..." if len(body) > 1000 else "")

        return f"""Classify this email:

**From:** {sender}
**Subject:** {subject}

**Body:**
{body_preview}

Analyze this email and provide classification in the following JSON format:
```json
{{
    "urgency": "urgent|high|normal|low|spam",
    "email_type": "inquiry|invoice|support|meeting|update|newsletter|personal",
    "confidence": "high|medium|low",
    "key_entities": {{
        "client_names": ["list of client/person names mentioned"],
        "deadlines": ["list of deadlines or dates mentioned"],
        "amounts": ["list of monetary amounts mentioned"],
        "action_items": ["list of action items or requests"]
    }},
    "suggested_actions": ["list of suggested next steps"],
    "reasoning": "Brief explanation of the classification",
    "priority_score": 1-10
}}
```

Respond with ONLY the JSON, no additional text.
"""

    def _parse_classification_response(self, response: str) -> dict:
        """Parse the classification response into structured data"""
        # Default classification
        result = {
            "urgency": "normal",
            "email_type": "personal",
            "confidence": "low",
            "key_entities": {
                "client_names": [],
                "deadlines": [],
                "amounts": [],
                "action_items": []
            },
            "suggested_actions": [],
            "reasoning": "Unable to classify",
            "priority_score": 5
        }

        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                result.update(parsed)
            else:
                # Try to find raw JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    parsed = json.loads(response[start:end])
                    result.update(parsed)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse classification JSON: {e}")
            logger.debug(f"Response was: {response[:200]}...")

        return result

    def should_create_action(self, classification: dict) -> bool:
        """
        Determine if an action file should be created based on classification.

        Args:
            classification: The classification result dict

        Returns:
            True if action file should be created
        """
        urgency = classification.get("urgency", "normal")
        email_type = classification.get("email_type", "personal")
        priority_score = classification.get("priority_score", 5)

        # Create action for urgent emails
        if urgency == "urgent":
            return True

        # Create action for high priority emails
        if urgency == "high" and priority_score >= 7:
            return True

        # Create action for important email types
        if email_type in ["inquiry", "invoice", "support"] and urgency in ["high", "normal"]:
            return True

        return False
