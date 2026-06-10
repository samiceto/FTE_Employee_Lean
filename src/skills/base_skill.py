"""
Base Skill Class for Silver Tier Compliance
All skills inherit from this base class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from groq import Groq
import time
from src.core.retry_handler import with_retry
from src.core.errors import NetworkTimeout, RateLimitExceeded, ServiceUnavailable
from src.logging.audit_logger import audit_logger


@dataclass
class SkillInput:
    """Input data for skill execution"""
    data: Any
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillOutput:
    """Output from skill execution"""
    result: Any
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """
    Base class for all agent skills.

    Skills are modular, reusable components that perform specific tasks.
    Each skill can optionally use the FREE Groq API for AI reasoning.
    """

    SKILL_NAME: str = "base_skill"
    REQUIRES_LLM: bool = False
    DESCRIPTION: str = "Base skill class"

    def __init__(self, vault_path: str, groq_api_key: Optional[str] = None,
                 groq_model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the skill.

        Args:
            vault_path: Path to the AI employee vault
            groq_api_key: Optional Groq API key (reads from env if not provided)
            groq_model: Groq model to use for LLM-based skills
        """
        self.vault_path = vault_path
        self.groq_model = groq_model

        # Initialize Groq client only if needed
        if self.REQUIRES_LLM:
            import os
            api_key = groq_api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    f"Skill {self.SKILL_NAME} requires LLM but GROQ_API_KEY not found"
                )
            self.groq_client = Groq(api_key=api_key)

    @abstractmethod
    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute the skill with given input.

        Args:
            input_data: SkillInput containing data and context

        Returns:
            SkillOutput with result and status
        """
        pass

    def run(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute the skill with audit logging.

        This is the recommended way to run skills as it provides
        comprehensive audit logging of all skill executions.

        Args:
            input_data: SkillInput containing data and context

        Returns:
            SkillOutput with result and status
        """
        # Log skill execution start
        audit_logger.log_skill_execution(
            skill_name=self.SKILL_NAME,
            input_data=input_data.data if isinstance(input_data.data, dict) else {'data': str(input_data.data)}
        )

        start_time = time.time()

        try:
            # Execute the skill
            result = self.execute(input_data)
            duration_ms = (time.time() - start_time) * 1000

            # Log success or failure
            if result.success:
                result_summary = ""
                if isinstance(result.result, dict):
                    # Create a brief summary for logging
                    result_summary = f"{len(result.result)} keys" if result.result else "empty"
                elif isinstance(result.result, list):
                    result_summary = f"{len(result.result)} items"
                elif result.result is not None:
                    result_summary = str(result.result)[:50]

                audit_logger.log_skill_success(
                    skill_name=self.SKILL_NAME,
                    duration_ms=duration_ms,
                    result_summary=result_summary
                )
            else:
                audit_logger.log_skill_failure(
                    skill_name=self.SKILL_NAME,
                    error=result.error_message or "Unknown error",
                    duration_ms=duration_ms
                )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_message = str(e)

            # Log skill failure
            audit_logger.log_skill_failure(
                skill_name=self.SKILL_NAME,
                error=error_message,
                duration_ms=duration_ms
            )

            # Return failure result
            return SkillOutput(
                result=None,
                success=False,
                error_message=error_message
            )

    @with_retry(max_attempts=3, base_delay=1, max_delay=60)
    def _call_groq(self, system_prompt: str, user_prompt: str,
                   temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """
        Helper method to call FREE Groq API with timeout and retry.

        Args:
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Response text from Groq

        Raises:
            NetworkTimeout: If the API call times out
            RateLimitExceeded: If rate limit is hit
            ServiceUnavailable: If Groq service is unavailable
        """
        if not self.REQUIRES_LLM:
            raise RuntimeError(f"Skill {self.SKILL_NAME} does not use LLM")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30  # 30 second timeout
            )
            return response.choices[0].message.content or ""
        except TimeoutError as e:
            raise NetworkTimeout(f"Groq API timeout: {e}")
        except Exception as e:
            error_str = str(e).lower()
            if '429' in str(e) or 'rate_limit' in error_str or 'rate limit' in error_str:
                raise RateLimitExceeded(f"Groq rate limit: {e}")
            elif 'unavailable' in error_str or 'service' in error_str:
                raise ServiceUnavailable(f"Groq unavailable: {e}")
            raise

    def validate_input(self, input_data: SkillInput, required_keys: list[str]) -> Optional[str]:
        """
        Validate that input data contains required keys.

        Args:
            input_data: Input to validate
            required_keys: List of required keys in input_data.data

        Returns:
            Error message if validation fails, None otherwise
        """
        if not isinstance(input_data.data, dict):
            return f"Input data must be a dictionary, got {type(input_data.data)}"

        missing_keys = [key for key in required_keys if key not in input_data.data]
        if missing_keys:
            return f"Missing required keys: {', '.join(missing_keys)}"

        return None
