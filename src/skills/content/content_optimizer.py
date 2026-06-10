"""
ContentOptimizer Skill - Optimizes social media content using Groq LLM
NEW skill for Silver Tier compliance
"""
import logging
from typing import Optional

from ..base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class ContentOptimizer(BaseSkill):
    """
    Optimizes social media content for maximum engagement.

    This skill uses Groq LLM to improve social media posts by:
    - Analyzing tone and clarity
    - Suggesting hashtags
    - Optimizing for platform-specific best practices
    - Improving engagement potential

    USES Groq API - Free but requires API key.
    """

    SKILL_NAME = "content_optimizer"
    REQUIRES_LLM = True
    DESCRIPTION = "Optimize social media content for engagement using Groq"

    SYSTEM_PROMPT = """You are a social media content optimization expert.
Your role is to analyze and improve social media posts for maximum engagement.

Consider:
1. Platform-specific best practices (LinkedIn, Instagram, X/Twitter)
2. Tone and voice (professional, casual, authentic)
3. Clarity and conciseness
4. Call-to-action effectiveness
5. Hashtag strategy
6. Emoji usage (when appropriate)

Provide actionable suggestions to improve posts while maintaining the original message."""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Optimize social media content.

        Args:
            input_data: SkillInput with data containing:
                - content: Original post content (required)
                - platform: Target platform (linkedin, instagram, x) (required)
                - tone: Desired tone (optional, default: "professional")

        Returns:
            SkillOutput with optimized content and suggestions
        """
        # Validate input
        error = self.validate_input(input_data, ["content", "platform"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            content = input_data.data["content"]
            platform = input_data.data["platform"].lower()
            tone = input_data.data.get("tone", "professional")

            # Validate platform
            if platform not in ["linkedin", "instagram", "x", "twitter"]:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message=f"Invalid platform: {platform}. Must be linkedin, instagram, or x"
                )

            # Build optimization prompt
            prompt = self._build_optimization_prompt(content, platform, tone)

            # Call Groq
            response = self._call_groq(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )

            # Parse response
            result = self._parse_optimization_response(response, content)

            return SkillOutput(
                result=result,
                success=True,
                metadata={
                    "platform": platform,
                    "tone": tone,
                    "original_length": len(content),
                    "optimized_length": len(result.get("optimized_content", ""))
                }
            )

        except Exception as e:
            logger.error(f"ContentOptimizer execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _build_optimization_prompt(self, content: str, platform: str, tone: str) -> str:
        """Build the prompt for content optimization"""
        platform_guidelines = {
            "linkedin": "Professional networking platform. Focus on insights, expertise, and value. Use line breaks for readability. 3-5 relevant hashtags.",
            "instagram": "Visual-first platform. Complement the image. Use storytelling. Emojis encouraged. 10-15 hashtags including niche and broad ones.",
            "x": "Concise and punchy. 280 character limit. Clear message. 1-3 hashtags max. Emojis sparingly.",
            "twitter": "Concise and punchy. 280 character limit. Clear message. 1-3 hashtags max. Emojis sparingly."
        }

        return f"""Optimize this social media post for {platform.upper()}.

**Original Content:**
{content}

**Platform Guidelines:**
{platform_guidelines.get(platform, "General social media best practices")}

**Desired Tone:** {tone}

Please provide:
1. **Optimized Content:** The improved version of the post
2. **Suggested Hashtags:** Relevant hashtags (if not already included)
3. **Improvements Made:** What you changed and why
4. **Engagement Tips:** Additional suggestions to boost engagement

Format your response as:
OPTIMIZED CONTENT:
[Your optimized version here]

SUGGESTED HASHTAGS:
[Hashtag suggestions here]

IMPROVEMENTS MADE:
[List of changes and reasoning]

ENGAGEMENT TIPS:
[Additional suggestions]
"""

    def _parse_optimization_response(self, response: str, original: str) -> dict:
        """Parse the optimization response into structured data"""
        result = {
            "optimized_content": original,  # Default to original if parsing fails
            "suggested_hashtags": [],
            "improvements_made": [],
            "engagement_tips": []
        }

        # Parse sections
        sections = {
            "OPTIMIZED CONTENT:": "optimized_content",
            "SUGGESTED HASHTAGS:": "suggested_hashtags",
            "IMPROVEMENTS MADE:": "improvements_made",
            "ENGAGEMENT TIPS:": "engagement_tips"
        }

        current_section = None
        current_content = []

        for line in response.split("\n"):
            line = line.strip()

            # Check if this line starts a new section
            section_found = False
            for header, key in sections.items():
                if line.upper().startswith(header):
                    # Save previous section
                    if current_section:
                        result[current_section] = self._process_section(
                            current_section, current_content
                        )
                    # Start new section
                    current_section = key
                    current_content = []
                    section_found = True
                    break

            if not section_found and current_section and line:
                current_content.append(line)

        # Save last section
        if current_section:
            result[current_section] = self._process_section(
                current_section, current_content
            )

        return result

    def _process_section(self, section_name: str, lines: list[str]) -> any:
        """Process a section's content based on its type"""
        if section_name == "optimized_content":
            return "\n".join(lines)
        elif section_name in ["suggested_hashtags", "improvements_made", "engagement_tips"]:
            # Return as list, removing bullet points and hashtag symbols
            return [
                line.lstrip("- •*#").strip()
                for line in lines
                if line and not line.startswith("---")
            ]
        else:
            return "\n".join(lines)
