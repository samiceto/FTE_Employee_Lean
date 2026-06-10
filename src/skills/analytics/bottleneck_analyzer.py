"""
BottleneckAnalyzer Skill - Analyze task patterns using LLM to identify bottlenecks and inefficiencies
"""
import logging
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class BottleneckAnalyzer(BaseSkill):
    """
    Analyze completed tasks using Groq LLM to identify operational bottlenecks.

    Uses LLM for qualitative pattern detection:
    - Repeated tasks (same issues recurring)
    - Complex tasks (descriptions suggesting time consumption)
    - Patterns suggesting manual intervention

    USES Groq API - Free.
    """

    SKILL_NAME = "bottleneck_analyzer"
    REQUIRES_LLM = True
    DESCRIPTION = "Analyze task patterns to identify bottlenecks using LLM"

    SYSTEM_PROMPT = """You are an expert business operations analyst specializing in identifying bottlenecks and inefficiencies.

Your task is to analyze completed tasks and identify:
1. Repeated tasks - Same or similar tasks that recur frequently (suggesting a process issue or lack of automation)
2. Complex tasks - Tasks with descriptions suggesting high time consumption or complexity
3. Manual intervention patterns - Tasks that should be automated but require manual work
4. Process inefficiencies - Any patterns suggesting workflow bottlenecks

Provide an efficiency score from 0-100 where:
- 90-100: Excellent efficiency, minimal bottlenecks
- 70-89: Good efficiency, minor optimizations possible
- 50-69: Moderate efficiency, clear opportunities for improvement
- 30-49: Low efficiency, significant bottlenecks present
- 0-29: Poor efficiency, major operational issues

Return ONLY valid JSON in this exact format:
{
    "bottlenecks": [
        {
            "task_type": "Category or pattern of tasks",
            "issue": "Specific bottleneck identified",
            "recommendation": "Actionable recommendation to address it"
        }
    ],
    "efficiency_score": 75,
    "patterns": ["List of efficiency patterns observed"]
}"""

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Analyze tasks to identify bottlenecks.

        Args:
            input_data: SkillInput with data containing:
                - tasks: List of task dictionaries (required)
                - execution_logs: Optional list of execution logs

        Returns:
            SkillOutput with bottleneck analysis

        Example:
            SkillInput(data={
                "tasks": [
                    {"title": "Fix bug in login", "category": "Development"},
                    {"title": "Fix bug in logout", "category": "Development"}
                ]
            })
        """
        # Validate input
        error = self.validate_input(input_data, ["tasks"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            tasks = input_data.data["tasks"]

            # Handle empty tasks
            if not tasks or len(tasks) == 0:
                logger.info("No tasks to analyze")
                return SkillOutput(
                    result={
                        "bottlenecks": [],
                        "efficiency_score": 100,
                        "patterns": ["No tasks completed this week - unable to analyze efficiency"]
                    },
                    success=True,
                    metadata={"task_count": 0}
                )

            # Prepare task summary for LLM
            task_summary = self._prepare_task_summary(tasks)

            # Build prompt
            prompt = f"""Analyze these {len(tasks)} completed tasks from this week:

{task_summary}

Identify bottlenecks, inefficiencies, and patterns. Provide actionable recommendations.
Return ONLY valid JSON. No markdown, no explanations."""

            # Call Groq
            try:
                response = self._call_groq(
                    system_prompt=self.SYSTEM_PROMPT,
                    user_prompt=prompt,
                    temperature=0.3,  # More consistent for analysis
                    max_tokens=2000
                )

                # Parse JSON response
                analysis = self._parse_json_response(response)

                if not analysis:
                    # Fallback to simple analysis
                    logger.warning("LLM JSON parsing failed, using fallback analysis")
                    analysis = self._fallback_analysis(tasks)

            except Exception as e:
                logger.error(f"Groq API call failed: {e}")
                # Fallback to simple analysis
                analysis = self._fallback_analysis(tasks)

            # Validate structure
            if "bottlenecks" not in analysis:
                analysis["bottlenecks"] = []
            if "efficiency_score" not in analysis:
                analysis["efficiency_score"] = 70  # Default moderate score
            if "patterns" not in analysis:
                analysis["patterns"] = []

            logger.info(f"Bottleneck analysis complete: {len(analysis['bottlenecks'])} bottlenecks identified, "
                       f"efficiency score: {analysis['efficiency_score']}")

            return SkillOutput(
                result=analysis,
                success=True,
                metadata={"task_count": len(tasks)}
            )

        except Exception as e:
            logger.error(f"BottleneckAnalyzer execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _prepare_task_summary(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Prepare a concise summary of tasks for LLM analysis.

        Args:
            tasks: List of task dictionaries

        Returns:
            Formatted task summary string
        """
        summary_lines = []

        # Group by category
        by_category = {}
        for task in tasks:
            category = task.get("category", "Uncategorized")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(task)

        # Format summary
        for category, category_tasks in by_category.items():
            summary_lines.append(f"\n{category} ({len(category_tasks)} tasks):")
            for task in category_tasks[:10]:  # Limit to 10 per category
                title = task.get("title", "Untitled")
                summary_lines.append(f"  - {title}")

            if len(category_tasks) > 10:
                summary_lines.append(f"  ... and {len(category_tasks) - 10} more")

        return "\n".join(summary_lines)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Args:
            response: LLM response string

        Returns:
            Parsed dictionary or None
        """
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

    def _fallback_analysis(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide simple rule-based analysis if LLM fails.

        Args:
            tasks: List of task dictionaries

        Returns:
            Basic analysis dictionary
        """
        bottlenecks = []
        patterns = []

        # Count tasks by category
        by_category = {}
        for task in tasks:
            category = task.get("category", "Uncategorized")
            by_category[category] = by_category.get(category, 0) + 1

        # Check for repeated patterns in titles
        title_words = {}
        for task in tasks:
            title = task.get("title", "").lower()
            for word in title.split():
                if len(word) > 4:  # Skip short words
                    title_words[word] = title_words.get(word, 0) + 1

        # Find repeated keywords
        repeated_keywords = [word for word, count in title_words.items() if count >= 3]

        if repeated_keywords:
            bottlenecks.append({
                "task_type": "Recurring Issues",
                "issue": f"Multiple tasks with similar keywords: {', '.join(repeated_keywords[:3])}",
                "recommendation": "Consider addressing root cause to prevent task recurrence"
            })

        # High volume in single category
        for category, count in by_category.items():
            if count >= len(tasks) * 0.5:  # 50% or more
                bottlenecks.append({
                    "task_type": category,
                    "issue": f"High concentration of tasks in {category} ({count} tasks)",
                    "recommendation": f"Review {category} processes for potential automation or optimization"
                })

        # Calculate simple efficiency score
        efficiency_score = max(30, min(100, 100 - (len(bottlenecks) * 15)))

        patterns.append(f"Completed {len(tasks)} tasks across {len(by_category)} categories")
        if repeated_keywords:
            patterns.append(f"Recurring keywords detected: {', '.join(repeated_keywords[:3])}")

        return {
            "bottlenecks": bottlenecks,
            "efficiency_score": efficiency_score,
            "patterns": patterns
        }
