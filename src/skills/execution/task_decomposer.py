"""
TaskDecomposer Skill - Breaks Plan.md into executable tasks with skill mappings
Uses Groq LLM (FREE) to intelligently map actions to skills
"""
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from models.execution_state import ExecutableTask, TaskStatus


class TaskDecomposer(BaseSkill):
    """
    Decomposes Plan.md files into executable tasks.

    Uses Groq LLM to:
    - Parse plan steps
    - Map actions to appropriate skills
    - Generate skill input parameters
    - Identify dependencies
    - Calculate priorities
    """

    SKILL_NAME = "task_decomposer"
    REQUIRES_LLM = True
    DESCRIPTION = "Breaks Plan.md into executable tasks with skill mappings using Groq LLM (FREE)"

    def __init__(self, vault_path: str, groq_api_key: str, groq_model: str = "llama-3.3-70b-versatile", **kwargs):
        super().__init__(vault_path, groq_api_key=groq_api_key, groq_model=groq_model, **kwargs)
        self.skill_registry_info = None  # Will be set from context

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Decompose plan into executable tasks.

        Input:
            data = {
                "plan_path": "path/to/Plan.md"
            }
            context = {
                "skill_registry": registry instance (optional)
            }

        Output:
            result = List[ExecutableTask]
        """
        try:
            plan_path = Path(input_data.data["plan_path"])

            if not plan_path.exists():
                return SkillOutput(
                    result=[],
                    success=False,
                    error_message=f"Plan file not found: {plan_path}"
                )

            # Read plan content
            plan_content = plan_path.read_text()

            # Extract goal/title from plan
            goal = self._extract_goal(plan_content)

            # Get available skills from context or use defaults
            skill_registry = input_data.context.get("skill_registry")
            available_skills = self._get_available_skills(skill_registry)

            # Parse plan steps
            steps = self._parse_plan_steps(plan_content)

            if not steps:
                return SkillOutput(
                    result=[],
                    success=True,
                    metadata={"message": "No action steps found in plan"}
                )

            # Use Groq LLM to decompose steps into tasks
            tasks = self._decompose_with_llm(steps, available_skills, goal)

            return SkillOutput(
                result=tasks,
                success=True,
                metadata={
                    "plan_path": str(plan_path),
                    "goal": goal,
                    "steps_count": len(steps),
                    "tasks_count": len(tasks)
                }
            )

        except Exception as e:
            return SkillOutput(
                result=[],
                success=False,
                error_message=f"Task decomposition failed: {str(e)}"
            )

    def _extract_goal(self, plan_content: str) -> str:
        """Extract goal from plan YAML frontmatter or title"""
        # Try YAML frontmatter first
        yaml_match = re.search(r'---\s*\n(.*?)\n---', plan_content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            goal_match = re.search(r'goal:\s*(.+)', yaml_content)
            if goal_match:
                return goal_match.group(1).strip()
            title_match = re.search(r'title:\s*(.+)', yaml_content)
            if title_match:
                return title_match.group(1).strip()

        # Fallback to first heading
        heading_match = re.search(r'^#\s+(.+)$', plan_content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        return "Execute Plan"

    def _parse_plan_steps(self, plan_content: str) -> List[Dict[str, Any]]:
        """Parse action steps from plan"""
        steps = []

        # Find "Action Steps" section
        steps_section_match = re.search(
            r'##\s+Action Steps(.*?)(?=\n##|\Z)',
            plan_content,
            re.DOTALL | re.IGNORECASE
        )

        if not steps_section_match:
            return steps

        steps_text = steps_section_match.group(1)

        # Try parsing markdown header format first (### Step 1: Title)
        step_pattern_headers = r'###\s+Step\s+(\d+):\s+(.+?)(?=\n###\s+Step|\Z)'
        matches = list(re.finditer(step_pattern_headers, steps_text, re.DOTALL))

        if not matches:
            # Fallback to simple numbered format (1. Title)
            step_pattern = r'(\d+)\.\s+(.+?)(?=\n\d+\.|\Z)'
            matches = list(re.finditer(step_pattern, steps_text, re.DOTALL))

        for match in matches:
            step_num = int(match.group(1))
            step_text = match.group(2).strip()

            # Extract metadata from step text
            assignee = "automated"
            if "human" in step_text.lower() or "manual" in step_text.lower():
                assignee = "human"
            elif "hybrid" in step_text.lower():
                assignee = "hybrid"

            steps.append({
                "number": step_num,
                "text": step_text,
                "assignee": assignee
            })

        return steps

    def _get_available_skills(self, skill_registry) -> List[Dict[str, str]]:
        """Get list of available skills with descriptions"""
        if skill_registry:
            try:
                skills_info = skill_registry.list_skills()
                return [
                    {
                        "name": name,
                        "description": info.get("description", "")
                    }
                    for name, info in skills_info.items()
                ]
            except:
                pass

        # Fallback to common skills
        return [
            {"name": "email_classifier", "description": "Classify emails by urgency and type"},
            {"name": "content_optimizer", "description": "Optimize content for social media platforms"},
            {"name": "invoice_generator", "description": "Generate invoices from data"},
            {"name": "expense_tracker", "description": "Track and categorize expenses"},
            {"name": "odoo_connector", "description": "Connect to Odoo ERP system"},
            {"name": "task_analyzer", "description": "Analyze and prioritize tasks"},
            {"name": "plan_generator", "description": "Generate execution plans"}
        ]

    def _decompose_with_llm(self, steps: List[Dict[str, Any]], available_skills: List[Dict[str, str]], goal: str) -> List[ExecutableTask]:
        """Use Groq LLM to decompose steps into executable tasks"""

        # Create list of skill names for strict validation
        skill_names = [s["name"] for s in available_skills]
        skill_list_str = ", ".join(f'"{name}"' for name in skill_names)

        system_prompt = f"""You are a task decomposition expert. Break down plan steps into executable tasks.

CRITICAL RULE: You MUST use ONLY these exact skill names (no other names allowed):
{skill_list_str}

Available Skills with Descriptions:
{json.dumps(available_skills, indent=2)}

Skill Usage Guide:
- "email_classifier": Classify emails by urgency/type → input: {{"subject": str, "body": str, "sender": str}}
- "content_optimizer": Optimize content for platforms → input: {{"content": str, "platform": str, "tone": str}}
- "invoice_generator": Generate invoices → input: {{"amount": float, "client": str, ...}}
- "expense_tracker": Track expenses → input: {{"description": str}}
- "task_analyzer": Analyze tasks → input: {{"max_tasks": int}}
- "plan_generator": Generate plans → input: {{"tasks": list, "business_context": str}}
- "context_loader": Load business context → input: {{}}
- "odoo_connector": Connect to Odoo ERP → input: {{"operation": str, ...}}

For each step, create ONE task with:
- action: Brief description of what to do
- skill_name: EXACTLY one of the skill names listed above (must match exactly!)
- skill_input: Parameters dict for the skill
- dependencies: List of task IDs this depends on (format: ["task_1", "task_2"])
- priority: 1-10 (10 = highest)

STRICT REQUIREMENTS:
1. skill_name MUST be exactly one of: {skill_list_str}
2. DO NOT invent new skill names - this will cause execution failures
3. If no perfect match, use the closest available skill
4. For human-only tasks, use "task_analyzer" to log them
5. Keep it simple - 1 task per step preferred

Return ONLY a JSON array of tasks, no explanations."""

        user_prompt = f"""Goal: {goal}

Plan Steps to convert into executable tasks:
{json.dumps(steps, indent=2)}

Convert each step into a task using ONLY the available skill names.
Return JSON array only."""

        # Call Groq LLM
        response = self._call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3  # Lower temperature for consistency
        )

        # Extract JSON from response
        tasks_data = self._extract_json_array(response)

        # Validate and correct skill names
        valid_skill_names = {s["name"] for s in available_skills}

        # Convert to ExecutableTask objects
        tasks = []
        for idx, task_data in enumerate(tasks_data):
            skill_name = task_data.get("skill_name", "unknown")

            # Validate skill name exists
            if skill_name not in valid_skill_names:
                # Try to find closest match
                original_skill = skill_name
                skill_name = self._find_closest_skill(skill_name, valid_skill_names)
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid skill '{original_skill}' replaced with '{skill_name}'")

            task = ExecutableTask(
                id=f"task_{idx + 1}",
                action=task_data.get("action", "Unknown action"),
                skill_name=skill_name,
                skill_input=task_data.get("skill_input", {}),
                priority=task_data.get("priority", 5),
                dependencies=task_data.get("dependencies", []),
                status=TaskStatus.PENDING
            )
            tasks.append(task)

        return tasks

    def _find_closest_skill(self, invalid_skill: str, valid_skills: set) -> str:
        """Find closest matching skill name or default to task_analyzer"""
        invalid_lower = invalid_skill.lower()

        # Direct keyword matching
        if "email" in invalid_lower:
            return "email_classifier"
        elif "content" in invalid_lower or "social" in invalid_lower or "post" in invalid_lower:
            return "content_optimizer"
        elif "invoice" in invalid_lower:
            return "invoice_generator"
        elif "expense" in invalid_lower:
            return "expense_tracker"
        elif "odoo" in invalid_lower or "accounting" in invalid_lower:
            return "odoo_connector"
        elif "plan" in invalid_lower:
            return "plan_generator"
        elif "context" in invalid_lower:
            return "context_loader"
        else:
            # Default fallback
            return "task_analyzer"

    def _extract_json_array(self, response: str) -> List[Dict[str, Any]]:
        """Extract JSON array from LLM response"""
        # Try to find JSON array in response
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing entire response
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "tasks" in data:
                return data["tasks"]
        except json.JSONDecodeError:
            pass

        # Fallback: create a simple task
        return [{
            "action": "Execute plan manually",
            "skill_name": "manual_execution",
            "skill_input": {},
            "dependencies": [],
            "priority": 5
        }]
