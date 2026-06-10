"""
ContextLoader Skill - Loads business context from vault
Extracted from reasoning_agent.py (lines 105-119)
"""
import logging
from pathlib import Path

from ..base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class ContextLoader(BaseSkill):
    """
    Loads business context from Business_Goals.md and Company_Handbook.md.

    This skill reads the business context files and returns their combined content
    for use in other skills (like plan generation).

    NO Groq API needed - pure file reading.
    """

    SKILL_NAME = "context_loader"
    REQUIRES_LLM = False
    DESCRIPTION = "Load business goals and company handbook"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Load business context from vault.

        Args:
            input_data: SkillInput (no data required)

        Returns:
            SkillOutput with combined business context string
        """
        try:
            context = self._load_business_context()

            return SkillOutput(
                result=context,
                success=True,
                metadata={"context_length": len(context)}
            )
        except Exception as e:
            logger.error(f"ContextLoader execution failed: {e}")
            return SkillOutput(
                result="",
                success=False,
                error_message=str(e)
            )

    def _load_business_context(self) -> str:
        """Load business goals and context from vault"""
        vault_path = Path(self.vault_path)
        context_parts = []

        # Load Business Goals
        goals_file = vault_path / "Business_Goals.md"
        if goals_file.exists():
            context_parts.append(f"## Business Goals\n{goals_file.read_text()}")
            logger.debug(f"Loaded Business_Goals.md ({goals_file.stat().st_size} bytes)")
        else:
            logger.warning(f"Business_Goals.md not found: {goals_file}")

        # Load Company Handbook
        handbook_file = vault_path / "Company_Handbook.md"
        if handbook_file.exists():
            context_parts.append(f"## Company Handbook\n{handbook_file.read_text()}")
            logger.debug(f"Loaded Company_Handbook.md ({handbook_file.stat().st_size} bytes)")
        else:
            logger.warning(f"Company_Handbook.md not found: {handbook_file}")

        result = "\n\n".join(context_parts) if context_parts else ""
        logger.info(f"Loaded business context ({len(result)} characters)")
        return result
