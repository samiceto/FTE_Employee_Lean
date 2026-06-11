"""
TaskAnalyzer Skill - Collects and parses tasks from Need_Action folder
Extracted from reasoning_agent.py (lines 121-173)
"""
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from ..base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


@dataclass
class TaskItem:
    """Represents a task item from Need_Action folder"""
    file_path: Path
    task_type: str
    content: str
    metadata: dict = field(default_factory=dict)
    priority: str = "normal"


class TaskAnalyzer(BaseSkill):
    """
    Analyzes and collects tasks from the Need_Action folder.

    This skill scans markdown files in Need_Action and its subfolders,
    parses YAML frontmatter, and returns structured TaskItem objects.

    NO Groq API needed - pure file parsing.
    """

    SKILL_NAME = "task_analyzer"
    REQUIRES_LLM = False
    DESCRIPTION = "Collect and parse tasks from Need_Action folder"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Collect tasks from Need_Action folder.

        Args:
            input_data: SkillInput with data containing:
                - max_tasks: Maximum number of tasks to collect (default: 20)

        Returns:
            SkillOutput with list of TaskItem objects
        """
        try:
            max_tasks = input_data.data.get("max_tasks", 20) if isinstance(input_data.data, dict) else 20
            tasks = self._collect_tasks(max_tasks)

            return SkillOutput(
                result=tasks,
                success=True,
                metadata={"task_count": len(tasks)}
            )
        except Exception as e:
            logger.error(f"TaskAnalyzer execution failed: {e}")
            return SkillOutput(
                result=[],
                success=False,
                error_message=str(e)
            )

    def _parse_markdown_file(self, file_path: Path) -> TaskItem:
        """Parse a markdown file from Need_Action into a TaskItem"""
        content = file_path.read_text(encoding="utf-8")
        metadata = {}
        body = content

        # Parse YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                body = parts[2].strip()

        task_type = metadata.get("type", "general")
        priority = metadata.get("priority", "normal")

        return TaskItem(
            file_path=file_path,
            task_type=task_type,
            content=body,
            metadata=metadata,
            priority=priority
        )

    def _collect_tasks(self, max_tasks: int = 20) -> list[TaskItem]:
        """Collect pending tasks from Need_Action folder (limited to avoid token limits)"""
        vault_path = Path(self.vault_path)
        needs_action = vault_path / "Need_Action"
        tasks = []

        if not needs_action.exists():
            logger.warning(f"Need_Action folder not found: {needs_action}")
            return tasks

        # Collect from root Need_Action
        for file_path in needs_action.glob("*.md"):
            tasks.append(self._parse_markdown_file(file_path))

        # Collect from subfolders
        for subfolder in ["email_replies", "business_tasks"]:
            subfolder_path = needs_action / subfolder
            if subfolder_path.exists():
                for file_path in subfolder_path.glob("*.md"):
                    tasks.append(self._parse_markdown_file(file_path))

        # Sort by priority (high priority first)
        priority_order = {"high": 0, "medium": 1, "normal": 2, "low": 3}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 2))

        # Limit tasks to avoid token limits on free tier APIs
        if len(tasks) > max_tasks:
            logger.warning(f"Limiting tasks from {len(tasks)} to {max_tasks}")
            tasks = tasks[:max_tasks]

        logger.info(f"Collected {len(tasks)} tasks from Need_Action")
        return tasks
