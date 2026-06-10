"""
Skill Registry - Auto-discovery and registration of skills
"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, Type, Optional

from .base_skill import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Registry for discovering and managing skills.

    Features:
    - Auto-discovery of skill classes from the skills directory
    - Skill instantiation with custom parameters
    - Skill lookup by name
    """

    def __init__(self):
        self._skills: Dict[str, Type[BaseSkill]] = {}
        self._instances: Dict[str, BaseSkill] = {}

    def register(self, skill_class: Type[BaseSkill]) -> None:
        """
        Manually register a skill class.

        Args:
            skill_class: Skill class to register (must inherit from BaseSkill)
        """
        if not issubclass(skill_class, BaseSkill):
            raise TypeError(f"{skill_class} must inherit from BaseSkill")

        skill_name = skill_class.SKILL_NAME
        if skill_name in self._skills:
            logger.warning(f"Skill {skill_name} already registered, overwriting")

        self._skills[skill_name] = skill_class
        logger.debug(f"Registered skill: {skill_name}")

    def get_skill(self, skill_name: str, **kwargs) -> BaseSkill:
        """
        Get an instance of a skill by name.

        Args:
            skill_name: Name of the skill to instantiate
            **kwargs: Arguments to pass to skill constructor

        Returns:
            Instance of the requested skill

        Raises:
            KeyError: If skill not found in registry
        """
        if skill_name not in self._skills:
            available = ", ".join(self._skills.keys())
            raise KeyError(
                f"Skill '{skill_name}' not found. Available skills: {available}"
            )

        # Create a cache key from skill name and kwargs
        cache_key = f"{skill_name}:{hash(frozenset(kwargs.items()))}"

        # Return cached instance if available
        if cache_key in self._instances:
            return self._instances[cache_key]

        # Create new instance
        skill_class = self._skills[skill_name]
        instance = skill_class(**kwargs)
        self._instances[cache_key] = instance

        return instance

    def auto_discover(self, skills_path: Path) -> int:
        """
        Auto-discover and register all skill classes from a directory.

        Scans the skills directory and its subdirectories for Python files,
        imports them, and registers any BaseSkill subclasses found.

        Args:
            skills_path: Path to the skills directory

        Returns:
            Number of skills discovered and registered
        """
        if not skills_path.exists():
            logger.warning(f"Skills path does not exist: {skills_path}")
            return 0

        count = 0

        # Find all Python files except __init__.py and base_skill.py
        for py_file in skills_path.rglob("*.py"):
            if py_file.name in ["__init__.py", "base_skill.py", "registry.py"]:
                continue

            # Convert file path to module path
            relative_path = py_file.relative_to(skills_path.parent)
            module_path = str(relative_path.with_suffix("")).replace("/", ".")

            try:
                # Import the module
                module = importlib.import_module(module_path)

                # Find all BaseSkill subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseSkill) and
                        obj is not BaseSkill and
                        obj.__module__ == module.__name__):
                        self.register(obj)
                        count += 1

            except Exception as e:
                logger.error(f"Failed to import {module_path}: {e}")

        logger.info(f"Auto-discovered {count} skills")
        return count

    def list_skills(self) -> Dict[str, str]:
        """
        Get a dictionary of all registered skills and their descriptions.

        Returns:
            Dictionary mapping skill names to descriptions
        """
        return {
            name: cls.DESCRIPTION
            for name, cls in self._skills.items()
        }

    def clear_cache(self) -> None:
        """Clear all cached skill instances"""
        self._instances.clear()


# Global registry instance
_global_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """
    Get the global skill registry instance.

    Returns:
        Global SkillRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)"""
    global _global_registry
    _global_registry = None
