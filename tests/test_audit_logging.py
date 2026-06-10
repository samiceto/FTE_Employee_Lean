"""
Unit tests for audit logging system.

Tests:
- AuditLogger singleton pattern
- Event logging (task, skill, MCP, error events)
- Log file creation and rotation
- Log cleanup and retention
- Event retrieval and filtering
- LogAnalyzer skill
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from src.logging.audit_logger import AuditLogger, AuditEventType
from src.skills.analytics.log_analyzer import LogAnalyzer
from src.skills.base_skill import SkillInput


class TestAuditLogger:
    """Test AuditLogger functionality"""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory"""
        with TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            audit_dir = vault_path / 'Logs' / 'audit'
            audit_dir.mkdir(parents=True, exist_ok=True)
            yield vault_path

    @pytest.fixture
    def logger(self, temp_vault, monkeypatch):
        """Create AuditLogger instance with temp vault"""
        # Reset singleton
        AuditLogger._instance = None

        # Patch environment variable
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        logger = AuditLogger()
        return logger

    def test_singleton_pattern(self, logger):
        """Test that AuditLogger follows singleton pattern"""
        logger2 = AuditLogger()
        assert logger is logger2

    def test_log_event_creates_file(self, logger, temp_vault):
        """Test that logging an event creates a log file"""
        logger.log_event(
            AuditEventType.TASK_START,
            component='test',
            message='Test message',
            success=True
        )

        # Check that log file was created
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'
        assert log_file.exists()

    def test_log_event_structure(self, logger, temp_vault):
        """Test that logged events have correct structure"""
        logger.log_event(
            AuditEventType.SKILL_EXECUTION,
            component='test_skill',
            message='Executing skill',
            metadata={'input': 'test'},
            success=True,
            duration_ms=100.5
        )

        # Read log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            event = json.loads(f.readline())

        # Verify structure
        assert 'timestamp' in event
        assert event['event_type'] == 'skill_execution'
        assert event['component'] == 'test_skill'
        assert event['message'] == 'Executing skill'
        assert event['success'] is True
        assert event['metadata'] == {'input': 'test'}
        assert event['duration_ms'] == 100.5

    def test_task_logging_methods(self, logger, temp_vault):
        """Test task-specific logging methods"""
        task_id = 'test_task_123'

        # Log task start
        logger.log_task_start(task_id, 'Test action', 'test_skill')

        # Log task complete
        logger.log_task_complete(task_id, 'Test action', 250.0)

        # Log task failed
        logger.log_task_failed(task_id, 'Test action', 'Test error', 3)

        # Read log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f]

        # Verify events
        assert len(events) == 3
        assert events[0]['event_type'] == 'task_start'
        assert events[1]['event_type'] == 'task_complete'
        assert events[1]['duration_ms'] == 250.0
        assert events[2]['event_type'] == 'task_failed'
        assert events[2]['success'] is False

    def test_skill_logging_methods(self, logger, temp_vault):
        """Test skill-specific logging methods"""
        logger.log_skill_execution('test_skill', {'key': 'value'})
        logger.log_skill_success('test_skill', 150.0, 'Result summary')
        logger.log_skill_failure('test_skill', 'Test error', 200.0)

        # Read events
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f]

        assert len(events) == 3
        assert events[0]['event_type'] == 'skill_execution'
        assert events[1]['event_type'] == 'skill_success'
        assert events[2]['event_type'] == 'skill_failure'
        assert events[2]['success'] is False

    def test_mcp_logging_methods(self, logger, temp_vault):
        """Test MCP-specific logging methods"""
        logger.log_mcp_call('odoo', 'create_invoice', {'partner': 'ABC Corp'})
        logger.log_mcp_success('odoo', 'create_invoice', 500.0)
        logger.log_mcp_failure('odoo', 'create_invoice', 'Connection error', 300.0)

        # Read events
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f]

        assert len(events) == 3
        assert events[0]['event_type'] == 'mcp_call'
        assert events[0]['component'] == 'mcp_odoo'
        assert events[1]['event_type'] == 'mcp_success'
        assert events[2]['event_type'] == 'mcp_failure'
        assert events[2]['success'] is False

    def test_error_logging_methods(self, logger, temp_vault):
        """Test error-specific logging methods"""
        logger.log_error('test_component', 'ValueError', 'Invalid input', {'input': 'test'})
        logger.log_error_recovered('test_component', 'retry', 3)
        logger.log_retry_attempt('test_component', 2, 3, 1.5)

        # Read events
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f]

        assert len(events) == 3
        assert events[0]['event_type'] == 'error_occurred'
        assert events[1]['event_type'] == 'error_recovered'
        assert events[2]['event_type'] == 'retry_attempt'

    def test_orchestrator_logging_methods(self, logger, temp_vault):
        """Test orchestrator-specific logging methods"""
        logger.log_orchestrator_start('ralph_wiggum_loop', 'Complete task', 'exec_123')
        logger.log_orchestrator_complete('ralph_wiggum_loop', 'exec_123', 5000.0, 10)

        # Read events
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = temp_vault / 'Logs' / 'audit' / f'audit_{date_str}.jsonl'

        with open(log_file, 'r') as f:
            events = [json.loads(line) for line in f]

        assert len(events) == 2
        assert events[0]['event_type'] == 'orchestrator_start'
        assert events[1]['event_type'] == 'orchestrator_complete'
        assert events[1]['duration_ms'] == 5000.0

    def test_get_recent_events(self, logger, temp_vault):
        """Test retrieving recent events with filtering"""
        # Create multiple events
        for i in range(5):
            logger.log_event(
                AuditEventType.TASK_START,
                component='test',
                message=f'Task {i}',
                success=True
            )

        for i in range(3):
            logger.log_event(
                AuditEventType.SKILL_EXECUTION,
                component='skill_test',
                message=f'Skill {i}',
                success=True
            )

        # Get all events
        events = logger.get_recent_events(limit=100)
        assert len(events) == 8

        # Filter by event type
        task_events = logger.get_recent_events(
            event_type=AuditEventType.TASK_START,
            limit=100
        )
        assert len(task_events) == 5

        # Filter by component
        skill_events = logger.get_recent_events(
            component='skill_test',
            limit=100
        )
        assert len(skill_events) == 3

        # Test limit
        limited_events = logger.get_recent_events(limit=3)
        assert len(limited_events) == 3

    def test_cleanup_old_logs(self, logger, temp_vault):
        """Test cleanup of old log files"""
        audit_dir = temp_vault / 'Logs' / 'audit'

        # Create old log file (35 days ago)
        old_date = datetime.now() - timedelta(days=35)
        old_file = audit_dir / f"audit_{old_date.strftime('%Y-%m-%d')}.jsonl"
        old_file.write_text('{"test": "old"}\n')

        # Create recent log file (5 days ago)
        recent_date = datetime.now() - timedelta(days=5)
        recent_file = audit_dir / f"audit_{recent_date.strftime('%Y-%m-%d')}.jsonl"
        recent_file.write_text('{"test": "recent"}\n')

        # Run cleanup (default 30 day retention)
        logger.cleanup_old_logs()

        # Old file should be deleted
        assert not old_file.exists()

        # Recent file should remain
        assert recent_file.exists()


class TestLogAnalyzer:
    """Test LogAnalyzer skill"""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault with sample logs"""
        with TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            audit_dir = vault_path / 'Logs' / 'audit'
            audit_dir.mkdir(parents=True, exist_ok=True)

            # Create sample log file
            date_str = datetime.now().strftime('%Y-%m-%d')
            log_file = audit_dir / f'audit_{date_str}.jsonl'

            # Write sample events
            events = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'task_start',
                    'component': 'task_executor',
                    'message': 'Task started',
                    'success': True,
                    'metadata': {},
                    'duration_ms': 100
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'skill_execution',
                    'component': 'test_skill',
                    'message': 'Skill executed',
                    'success': True,
                    'metadata': {},
                    'duration_ms': 200
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'skill_failure',
                    'component': 'test_skill',
                    'message': 'Skill failed',
                    'success': False,
                    'metadata': {},
                    'duration_ms': 150
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'mcp_call',
                    'component': 'mcp_odoo',
                    'message': 'MCP call',
                    'success': True,
                    'metadata': {},
                    'duration_ms': 500
                },
            ]

            with open(log_file, 'w') as f:
                for event in events:
                    f.write(json.dumps(event) + '\n')

            yield vault_path

    def test_log_analyzer_execution(self, temp_vault, monkeypatch):
        """Test LogAnalyzer skill execution"""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        analyzer = LogAnalyzer(vault_path=str(temp_vault))

        input_data = SkillInput(data={'days': 7, 'include_anomalies': True})
        result = analyzer.execute(input_data)

        assert result.success is True
        assert result.result is not None
        assert 'total_events' in result.result
        assert result.result['total_events'] == 4

    def test_log_analyzer_metrics(self, temp_vault, monkeypatch):
        """Test LogAnalyzer metrics calculation"""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        analyzer = LogAnalyzer(vault_path=str(temp_vault))

        input_data = SkillInput(data={'days': 7})
        result = analyzer.execute(input_data)

        metrics = result.result

        # Check overall metrics
        assert 'success_rate' in metrics
        assert 'total_events' in metrics
        assert 'avg_duration_ms' in metrics

        # Check component metrics
        assert 'component_metrics' in metrics
        assert 'test_skill' in metrics['component_metrics']

        # Check event distribution
        assert 'event_type_distribution' in metrics

        # Check error analysis
        assert 'error_analysis' in metrics
        assert metrics['error_analysis']['total_errors'] == 1

    def test_log_analyzer_no_logs(self, monkeypatch):
        """Test LogAnalyzer with no logs"""
        with TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            audit_dir = vault_path / 'Logs' / 'audit'
            audit_dir.mkdir(parents=True, exist_ok=True)

            monkeypatch.setenv('VAULT_PATH', str(vault_path))

            analyzer = LogAnalyzer(vault_path=str(vault_path))

            input_data = SkillInput(data={'days': 7})
            result = analyzer.execute(input_data)

            assert result.success is False
            assert 'error' in result.result
