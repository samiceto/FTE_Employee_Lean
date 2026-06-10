"""
Comprehensive audit logging system with structured JSON logging.

Provides centralized audit trail for all system operations including
task execution, skill invocation, MCP calls, and error events.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types"""
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    SKILL_EXECUTION = "skill_execution"
    SKILL_SUCCESS = "skill_success"
    SKILL_FAILURE = "skill_failure"
    MCP_CALL = "mcp_call"
    MCP_SUCCESS = "mcp_success"
    MCP_FAILURE = "mcp_failure"
    ERROR_OCCURRED = "error_occurred"
    ERROR_RECOVERED = "error_recovered"
    RETRY_ATTEMPT = "retry_attempt"
    QUEUE_ENQUEUE = "queue_enqueue"
    QUEUE_DEQUEUE = "queue_dequeue"
    DLQ_ADDED = "dlq_added"
    WATCHDOG_RESTART = "watchdog_restart"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ORCHESTRATOR_START = "orchestrator_start"
    ORCHESTRATOR_COMPLETE = "orchestrator_complete"


class AuditLogger:
    """
    Centralized audit logging system with structured JSON format.

    Features:
    - Structured JSON logging for all events
    - 30-day retention with automatic cleanup
    - Daily log rotation
    - Fast append-only writes
    - Searchable by event type, component, timestamp
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize audit logger (only once)"""
        if not self._initialized:
            self.vault_path = Path(os.getenv(
                'VAULT_PATH',
                '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'
            ))
            self.audit_dir = self.vault_path / 'Logs' / 'audit'
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            self.retention_days = int(os.getenv('AUDIT_RETENTION_DAYS', '30'))
            self._initialized = True
            logger.info(f"AuditLogger initialized with {self.retention_days} day retention")

    def _get_log_file(self) -> Path:
        """Get today's log file path"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return self.audit_dir / f"audit_{date_str}.jsonl"

    def log_event(
        self,
        event_type: AuditEventType,
        component: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_ms: Optional[float] = None
    ):
        """
        Log an audit event.

        Args:
            event_type: Type of event
            component: Component generating the event
            message: Human-readable message
            metadata: Additional event metadata
            success: Whether operation was successful
            duration_ms: Operation duration in milliseconds
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'component': component,
            'message': message,
            'success': success,
            'metadata': metadata or {}
        }

        if duration_ms is not None:
            event['duration_ms'] = duration_ms

        try:
            log_file = self._get_log_file()
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def log_task_start(self, task_id: str, action: str, skill_name: str):
        """Log task start event"""
        self.log_event(
            AuditEventType.TASK_START,
            'task_executor',
            f"Task {task_id} started: {action}",
            metadata={'task_id': task_id, 'action': action, 'skill_name': skill_name}
        )

    def log_task_complete(self, task_id: str, action: str, duration_ms: float):
        """Log task completion event"""
        self.log_event(
            AuditEventType.TASK_COMPLETE,
            'task_executor',
            f"Task {task_id} completed: {action}",
            metadata={'task_id': task_id, 'action': action},
            duration_ms=duration_ms
        )

    def log_task_failed(self, task_id: str, action: str, error: str, attempts: int):
        """Log task failure event"""
        self.log_event(
            AuditEventType.TASK_FAILED,
            'task_executor',
            f"Task {task_id} failed: {error}",
            metadata={'task_id': task_id, 'action': action, 'error': error, 'attempts': attempts},
            success=False
        )

    def log_skill_execution(self, skill_name: str, input_data: Dict[str, Any]):
        """Log skill execution start"""
        self.log_event(
            AuditEventType.SKILL_EXECUTION,
            skill_name,
            f"Executing skill: {skill_name}",
            metadata={'input_data': input_data}
        )

    def log_skill_success(self, skill_name: str, duration_ms: float, result_summary: str = ""):
        """Log skill success"""
        self.log_event(
            AuditEventType.SKILL_SUCCESS,
            skill_name,
            f"Skill {skill_name} succeeded: {result_summary}",
            metadata={'result_summary': result_summary},
            duration_ms=duration_ms
        )

    def log_skill_failure(self, skill_name: str, error: str, duration_ms: float):
        """Log skill failure"""
        self.log_event(
            AuditEventType.SKILL_FAILURE,
            skill_name,
            f"Skill {skill_name} failed: {error}",
            metadata={'error': error},
            success=False,
            duration_ms=duration_ms
        )

    def log_mcp_call(self, server: str, tool: str, arguments: Dict[str, Any]):
        """Log MCP server call"""
        self.log_event(
            AuditEventType.MCP_CALL,
            f"mcp_{server}",
            f"MCP call: {server}.{tool}",
            metadata={'server': server, 'tool': tool, 'arguments': arguments}
        )

    def log_mcp_success(self, server: str, tool: str, duration_ms: float):
        """Log MCP success"""
        self.log_event(
            AuditEventType.MCP_SUCCESS,
            f"mcp_{server}",
            f"MCP call succeeded: {server}.{tool}",
            metadata={'server': server, 'tool': tool},
            duration_ms=duration_ms
        )

    def log_mcp_failure(self, server: str, tool: str, error: str, duration_ms: float):
        """Log MCP failure"""
        self.log_event(
            AuditEventType.MCP_FAILURE,
            f"mcp_{server}",
            f"MCP call failed: {server}.{tool} - {error}",
            metadata={'server': server, 'tool': tool, 'error': error},
            success=False,
            duration_ms=duration_ms
        )

    def log_error(self, component: str, error_type: str, error_message: str, context: Dict[str, Any]):
        """Log error event"""
        self.log_event(
            AuditEventType.ERROR_OCCURRED,
            component,
            f"Error in {component}: {error_message}",
            metadata={'error_type': error_type, 'error_message': error_message, 'context': context},
            success=False
        )

    def log_error_recovered(self, component: str, recovery_method: str, attempts: int):
        """Log error recovery"""
        self.log_event(
            AuditEventType.ERROR_RECOVERED,
            component,
            f"Error recovered in {component} using {recovery_method}",
            metadata={'recovery_method': recovery_method, 'attempts': attempts}
        )

    def log_retry_attempt(self, component: str, attempt: int, max_attempts: int, delay_seconds: float):
        """Log retry attempt"""
        self.log_event(
            AuditEventType.RETRY_ATTEMPT,
            component,
            f"Retry attempt {attempt}/{max_attempts} after {delay_seconds}s",
            metadata={'attempt': attempt, 'max_attempts': max_attempts, 'delay_seconds': delay_seconds}
        )

    def log_queue_enqueue(self, queue_type: str, item_id: str, reason: str):
        """Log item added to queue"""
        self.log_event(
            AuditEventType.QUEUE_ENQUEUE,
            f"{queue_type}_queue",
            f"Item {item_id} queued: {reason}",
            metadata={'queue_type': queue_type, 'item_id': item_id, 'reason': reason}
        )

    def log_queue_dequeue(self, queue_type: str, item_id: str, queue_time_seconds: float):
        """Log item processed from queue"""
        self.log_event(
            AuditEventType.QUEUE_DEQUEUE,
            f"{queue_type}_queue",
            f"Item {item_id} dequeued after {queue_time_seconds}s",
            metadata={'queue_type': queue_type, 'item_id': item_id, 'queue_time_seconds': queue_time_seconds}
        )

    def log_dlq_added(self, task_id: str, error: str, attempts: int):
        """Log task moved to dead letter queue"""
        self.log_event(
            AuditEventType.DLQ_ADDED,
            'dead_letter_queue',
            f"Task {task_id} moved to DLQ after {attempts} attempts",
            metadata={'task_id': task_id, 'error': error, 'attempts': attempts},
            success=False
        )

    def log_watchdog_restart(self, process_name: str, reason: str, restart_count: int):
        """Log process restart by watchdog"""
        self.log_event(
            AuditEventType.WATCHDOG_RESTART,
            'watchdog',
            f"Process {process_name} restarted: {reason}",
            metadata={'process_name': process_name, 'reason': reason, 'restart_count': restart_count}
        )

    def log_orchestrator_start(self, orchestrator: str, goal: str, execution_id: str):
        """Log orchestrator start"""
        self.log_event(
            AuditEventType.ORCHESTRATOR_START,
            orchestrator,
            f"Orchestrator started: {goal}",
            metadata={'orchestrator': orchestrator, 'goal': goal, 'execution_id': execution_id}
        )

    def log_orchestrator_complete(self, orchestrator: str, execution_id: str, duration_ms: float, tasks_completed: int):
        """Log orchestrator completion"""
        self.log_event(
            AuditEventType.ORCHESTRATOR_COMPLETE,
            orchestrator,
            f"Orchestrator completed: {tasks_completed} tasks",
            metadata={'orchestrator': orchestrator, 'execution_id': execution_id, 'tasks_completed': tasks_completed},
            duration_ms=duration_ms
        )

    def cleanup_old_logs(self):
        """Remove logs older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for log_file in self.audit_dir.glob("audit_*.jsonl"):
            try:
                # Extract date from filename: audit_YYYY-MM-DD.jsonl
                date_str = log_file.stem.replace('audit_', '')
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Deleted old audit log: {log_file}")
            except Exception as e:
                logger.error(f"Failed to cleanup audit log {log_file}: {e}")

    def get_recent_events(
        self,
        event_type: Optional[AuditEventType] = None,
        component: Optional[str] = None,
        limit: int = 100,
        success_only: bool = False
    ) -> list:
        """
        Get recent audit events.

        Args:
            event_type: Filter by event type
            component: Filter by component
            limit: Maximum events to return
            success_only: Only return successful events

        Returns:
            List of event dictionaries
        """
        events = []

        # Get recent log files (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        log_files = sorted(
            [f for f in self.audit_dir.glob("audit_*.jsonl")
             if self._get_file_date(f) >= cutoff_date],
            reverse=True
        )

        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if len(events) >= limit:
                            return events

                        try:
                            event = json.loads(line.strip())

                            # Apply filters
                            if event_type and event['event_type'] != event_type.value:
                                continue
                            if component and event['component'] != component:
                                continue
                            if success_only and not event.get('success', True):
                                continue

                            events.append(event)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Failed to read audit log {log_file}: {e}")

        return events[:limit]

    def _get_file_date(self, log_file: Path) -> datetime:
        """Extract date from log filename"""
        try:
            date_str = log_file.stem.replace('audit_', '')
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return datetime.min


# Singleton instance
audit_logger = AuditLogger()
