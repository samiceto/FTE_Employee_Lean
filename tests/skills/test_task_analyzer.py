"""
Tests for TaskAnalyzer skill
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from src.skills.analysis.task_analyzer import TaskAnalyzer
from src.skills import SkillInput


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing"""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "test_vault"
    vault_path.mkdir()

    # Create Need_Action structure
    need_action = vault_path / "Need_Action"
    need_action.mkdir()
    (need_action / "email_replies").mkdir()
    (need_action / "business_tasks").mkdir()

    yield str(vault_path)

    # Cleanup
    shutil.rmtree(temp_dir)


def test_task_analyzer_initialization(temp_vault):
    """Test TaskAnalyzer can be initialized"""
    analyzer = TaskAnalyzer(vault_path=temp_vault)
    assert analyzer.SKILL_NAME == "task_analyzer"
    assert analyzer.REQUIRES_LLM == False


def test_task_analyzer_empty_folder(temp_vault):
    """Test TaskAnalyzer with no tasks"""
    analyzer = TaskAnalyzer(vault_path=temp_vault)
    input_data = SkillInput(data={"max_tasks": 10})

    result = analyzer.execute(input_data)

    assert result.success == True
    assert result.result == []
    assert result.metadata["task_count"] == 0


def test_task_analyzer_with_tasks(temp_vault):
    """Test TaskAnalyzer with actual task files"""
    analyzer = TaskAnalyzer(vault_path=temp_vault)

    # Create test task files
    need_action = Path(temp_vault) / "Need_Action"

    task1 = need_action / "task1.md"
    task1.write_text("""---
type: email_reply
priority: high
---
Reply to client about project deadline.""")

    task2 = need_action / "email_replies" / "task2.md"
    task2.write_text("""---
type: business_task
priority: normal
---
Update invoice for client XYZ.""")

    # Execute skill
    input_data = SkillInput(data={"max_tasks": 10})
    result = analyzer.execute(input_data)

    assert result.success == True
    assert len(result.result) == 2
    assert result.metadata["task_count"] == 2

    # Check priority sorting (high priority first)
    assert result.result[0].priority == "high"
    assert result.result[1].priority == "normal"


def test_task_analyzer_max_tasks_limit(temp_vault):
    """Test TaskAnalyzer respects max_tasks limit"""
    analyzer = TaskAnalyzer(vault_path=temp_vault)

    # Create 5 test tasks
    need_action = Path(temp_vault) / "Need_Action"
    for i in range(5):
        task = need_action / f"task{i}.md"
        task.write_text(f"Task {i} content")

    # Request only 3 tasks
    input_data = SkillInput(data={"max_tasks": 3})
    result = analyzer.execute(input_data)

    assert result.success == True
    assert len(result.result) == 3


def test_task_analyzer_yaml_parsing(temp_vault):
    """Test TaskAnalyzer parses YAML frontmatter correctly"""
    analyzer = TaskAnalyzer(vault_path=temp_vault)

    need_action = Path(temp_vault) / "Need_Action"
    task = need_action / "task_with_metadata.md"
    task.write_text("""---
type: invoice
priority: high
client: ABC Corp
amount: $5000
---
Invoice for Q4 services""")

    input_data = SkillInput(data={"max_tasks": 10})
    result = analyzer.execute(input_data)

    assert result.success == True
    task_item = result.result[0]
    assert task_item.task_type == "invoice"
    assert task_item.priority == "high"
    assert task_item.metadata["client"] == "ABC Corp"
    assert task_item.content == "Invoice for Q4 services"
