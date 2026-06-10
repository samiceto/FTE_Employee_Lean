"""
WeeklyTaskCollector Skill - Scan Done/ folder for completed tasks within date range
"""
import logging
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class WeeklyTaskCollector(BaseSkill):
    """
    Scan Done/ folder for completed tasks within a specific date range.

    This skill parses task files in the Done/ folder, extracting metadata
    from YAML frontmatter and using file modification times as fallback.

    Does NOT use LLM - Pure Python file parsing.
    """

    SKILL_NAME = "weekly_task_collector"
    REQUIRES_LLM = False
    DESCRIPTION = "Collect completed tasks from Done/ folder within date range"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Collect tasks completed within the specified date range.

        Args:
            input_data: SkillInput with data containing:
                - start_date: ISO format date string (required)
                - end_date: ISO format date string (required)

        Returns:
            SkillOutput with:
                - tasks: List of task dictionaries
                - total_tasks: Count of tasks
                - by_category: Dictionary of tasks grouped by category

        Example:
            SkillInput(data={
                "start_date": "2026-01-15",
                "end_date": "2026-01-21"
            })
        """
        # Validate input
        error = self.validate_input(input_data, ["start_date", "end_date"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            start_date = datetime.fromisoformat(input_data.data["start_date"])
            end_date = datetime.fromisoformat(input_data.data["end_date"])

            # Get Done folder path
            done_folder = Path(self.vault_path) / "Done"

            if not done_folder.exists():
                logger.warning(f"Done folder not found at {done_folder}")
                return SkillOutput(
                    result={
                        "tasks": [],
                        "total_tasks": 0,
                        "by_category": {}
                    },
                    success=True,
                    metadata={"warning": "Done folder not found"}
                )

            # Collect tasks
            tasks = []
            by_category = {}

            # Scan all markdown files in Done/
            for task_file in done_folder.glob("**/*.md"):
                try:
                    task_data = self._parse_task_file(task_file, start_date, end_date)
                    if task_data:
                        tasks.append(task_data)

                        # Group by category
                        category = task_data.get("category", "Uncategorized")
                        if category not in by_category:
                            by_category[category] = []
                        by_category[category].append(task_data)

                except Exception as e:
                    logger.error(f"Error parsing task file {task_file}: {e}")
                    continue

            logger.info(f"Collected {len(tasks)} tasks from {start_date.date()} to {end_date.date()}")

            return SkillOutput(
                result={
                    "tasks": tasks,
                    "total_tasks": len(tasks),
                    "by_category": {cat: len(tasks) for cat, tasks in by_category.items()}
                },
                success=True,
                metadata={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "files_scanned": len(list(done_folder.glob("**/*.md")))
                }
            )

        except Exception as e:
            logger.error(f"WeeklyTaskCollector execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _parse_task_file(self, file_path: Path, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Parse a task file and check if it falls within the date range.

        Args:
            file_path: Path to task file
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Task dictionary if within date range, None otherwise
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Parse YAML frontmatter
            metadata = self._parse_frontmatter(content)

            # Get completion date (from metadata or file mtime)
            completed_date = None

            if metadata.get("completed_date"):
                try:
                    completed_date = datetime.fromisoformat(metadata["completed_date"])
                except ValueError:
                    pass

            # Fallback to file modification time
            if not completed_date:
                mtime = file_path.stat().st_mtime
                completed_date = datetime.fromtimestamp(mtime)

            # Check if within date range
            if not (start_date <= completed_date <= end_date):
                return None

            # Extract title (from metadata or first heading)
            title = metadata.get("title") or self._extract_title(content)

            return {
                "title": title,
                "completed_date": completed_date.isoformat(),
                "file_path": str(file_path.relative_to(self.vault_path)),
                "category": metadata.get("category") or metadata.get("type") or "Uncategorized",
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Error parsing task file {file_path}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown file content

        Returns:
            Dictionary of frontmatter fields
        """
        metadata = {}

        # Check for YAML frontmatter (--- at start)
        if not content.startswith("---"):
            return metadata

        try:
            # Extract frontmatter section
            parts = content.split("---", 2)
            if len(parts) < 3:
                return metadata

            frontmatter = parts[1].strip()

            # Parse simple YAML (key: value pairs)
            for line in frontmatter.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

        except Exception as e:
            logger.debug(f"Error parsing frontmatter: {e}")

        return metadata

    def _extract_title(self, content: str) -> str:
        """
        Extract title from markdown content (first heading).

        Args:
            content: Markdown file content

        Returns:
            Title string
        """
        # Remove frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        # Find first heading
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Remove # characters
                title = re.sub(r"^#+\s*", "", line)
                return title.strip()

        return "Untitled Task"
