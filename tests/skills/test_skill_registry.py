"""
Tests for SkillRegistry
"""
import pytest
from pathlib import Path

from src.skills import SkillRegistry, BaseSkill, SkillInput, SkillOutput, reset_registry


class MockSkill(BaseSkill):
    """Mock skill for testing"""
    SKILL_NAME = "mock_skill"
    REQUIRES_LLM = False
    DESCRIPTION = "A mock skill for testing"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        return SkillOutput(result="mock_result", success=True)


def test_registry_initialization():
    """Test SkillRegistry can be initialized"""
    registry = SkillRegistry()
    assert len(registry._skills) == 0


def test_registry_manual_registration():
    """Test manually registering a skill"""
    registry = SkillRegistry()
    registry.register(MockSkill)

    assert "mock_skill" in registry._skills
    assert registry._skills["mock_skill"] == MockSkill


def test_registry_get_skill():
    """Test getting a skill instance"""
    registry = SkillRegistry()
    registry.register(MockSkill)

    skill = registry.get_skill("mock_skill", vault_path="/tmp/test")

    assert isinstance(skill, MockSkill)
    assert skill.vault_path == "/tmp/test"


def test_registry_get_nonexistent_skill():
    """Test getting a skill that doesn't exist"""
    registry = SkillRegistry()

    with pytest.raises(KeyError) as exc_info:
        registry.get_skill("nonexistent_skill", vault_path="/tmp/test")

    assert "not found" in str(exc_info.value)


def test_registry_list_skills():
    """Test listing all registered skills"""
    registry = SkillRegistry()
    registry.register(MockSkill)

    skills = registry.list_skills()

    assert "mock_skill" in skills
    assert skills["mock_skill"] == "A mock skill for testing"


def test_registry_caching():
    """Test that skill instances are cached"""
    registry = SkillRegistry()
    registry.register(MockSkill)

    skill1 = registry.get_skill("mock_skill", vault_path="/tmp/test")
    skill2 = registry.get_skill("mock_skill", vault_path="/tmp/test")

    # Should return the same cached instance
    assert skill1 is skill2


def test_registry_clear_cache():
    """Test clearing the skill cache"""
    registry = SkillRegistry()
    registry.register(MockSkill)

    skill1 = registry.get_skill("mock_skill", vault_path="/tmp/test")
    registry.clear_cache()
    skill2 = registry.get_skill("mock_skill", vault_path="/tmp/test")

    # Should create a new instance after cache clear
    assert skill1 is not skill2


def test_registry_auto_discover():
    """Test auto-discovery of skills from directory"""
    registry = SkillRegistry()

    # Point to the actual skills directory
    skills_path = Path(__file__).parent.parent.parent / "src" / "skills"

    if skills_path.exists():
        count = registry.auto_discover(skills_path)

        # Should discover at least our core skills
        assert count >= 5  # TaskAnalyzer, ContextLoader, PlanGenerator, ContentOptimizer, EmailClassifier
        assert "task_analyzer" in registry._skills
        assert "context_loader" in registry._skills
        assert "plan_generator" in registry._skills


def test_global_registry():
    """Test the global registry singleton"""
    from src.skills import get_registry

    reset_registry()  # Start fresh

    registry1 = get_registry()
    registry2 = get_registry()

    # Should return the same instance
    assert registry1 is registry2
