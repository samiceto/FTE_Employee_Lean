"""
Execution State Models for Ralph Wiggum Loop
Data structures for tracking autonomous execution state
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class ExecutionPhase(Enum):
    """Execution phase in the Ralph Wiggum Loop"""
    PLANNING = "planning"
    DECOMPOSING = "decomposing"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    ADJUSTING = "adjusting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutableTask:
    """
    A single executable task with dependencies and error handling
    """
    id: str
    action: str
    skill_name: str
    skill_input: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    dependencies: List[str] = field(default_factory=list)

    # Error handling
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None

    # Results
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutableTask':
        """Create from dictionary with enum handling"""
        data = data.copy()
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)

    def mark_in_progress(self):
        """Mark task as in progress"""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now().isoformat()

    def mark_completed(self, result: Any = None, metadata: Dict[str, Any] = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        if metadata:
            self.metadata.update(metadata)
        self.updated_at = datetime.now().isoformat()

    def mark_failed(self, error_message: str, vault_path: Optional[Path] = None):
        """
        Mark task as failed, retry if attempts remain, else send to DLQ.

        Args:
            error_message: Error message describing the failure
            vault_path: Path to vault for dead letter queue (optional)
        """
        self.attempts += 1
        self.error_message = error_message
        self.updated_at = datetime.now().isoformat()

        if self.attempts < self.max_attempts:
            # Reset to PENDING for retry
            self.status = TaskStatus.PENDING
            logger.warning(
                f"Task {self.id} failed (attempt {self.attempts}/{self.max_attempts}), "
                f"will retry: {error_message}"
            )
        else:
            # Max attempts reached - send to dead letter queue
            self.status = TaskStatus.FAILED
            logger.error(
                f"Task {self.id} failed after {self.attempts} attempts, "
                f"moving to dead letter queue: {error_message}"
            )

            if vault_path:
                try:
                    from src.core.dead_letter_queue import DeadLetterQueue
                    dlq = DeadLetterQueue(vault_path)
                    dlq.add_failed_task(self, error_message)
                except Exception as e:
                    logger.error(f"Failed to add task to dead letter queue: {e}")

    def mark_blocked(self, reason: str):
        """Mark task as blocked"""
        self.status = TaskStatus.BLOCKED
        self.error_message = reason
        self.updated_at = datetime.now().isoformat()

    def mark_skipped(self, reason: str):
        """Mark task as skipped"""
        self.status = TaskStatus.SKIPPED
        self.error_message = reason
        self.updated_at = datetime.now().isoformat()

    def can_execute(self, completed_task_ids: set) -> bool:
        """Check if task can be executed based on dependencies"""
        if self.status not in [TaskStatus.PENDING]:
            return False

        # Check all dependencies are completed
        return all(dep_id in completed_task_ids for dep_id in self.dependencies)


@dataclass
class EvaluationResult:
    """Result of progress evaluation"""
    on_track: bool
    confidence: str  # "high", "medium", "low"
    needs_adjustment: bool
    blocking_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    should_continue: bool = True
    reasoning: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ExecutionState:
    """
    Complete state of execution for Ralph Wiggum Loop
    Tracks all tasks, progress, and execution metadata
    """
    # Execution metadata
    execution_id: str
    plan_path: str
    goal: str
    phase: ExecutionPhase = ExecutionPhase.PLANNING

    # Task tracking
    tasks: List[ExecutableTask] = field(default_factory=list)

    # Progress tracking
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0
    tasks_total: int = 0

    # Loop control
    iteration: int = 0
    max_iterations: int = 10
    is_running: bool = True
    needs_adjustment: bool = False

    # Evaluation history
    last_evaluation: Optional[EvaluationResult] = None
    adjustments_made: List[Dict[str, Any]] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum handling"""
        data = asdict(self)
        data['phase'] = self.phase.value
        data['tasks'] = [task.to_dict() for task in self.tasks]
        if self.last_evaluation:
            data['last_evaluation'] = self.last_evaluation.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionState':
        """Create from dictionary with enum handling"""
        data = data.copy()

        # Handle phase enum
        if isinstance(data.get('phase'), str):
            data['phase'] = ExecutionPhase(data['phase'])

        # Handle tasks
        if 'tasks' in data:
            data['tasks'] = [ExecutableTask.from_dict(t) for t in data['tasks']]

        # Handle evaluation
        if data.get('last_evaluation'):
            data['last_evaluation'] = EvaluationResult.from_dict(data['last_evaluation'])

        return cls(**data)

    def save(self, vault_path: Path) -> Path:
        """Save state to active execution file"""
        state_dir = vault_path / "ExecutionState"
        state_dir.mkdir(exist_ok=True)

        state_file = state_dir / "active_execution.json"

        with open(state_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return state_file

    @classmethod
    def load(cls, vault_path: Path) -> Optional['ExecutionState']:
        """Load active execution state"""
        state_file = vault_path / "ExecutionState" / "active_execution.json"

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)

    def archive(self, vault_path: Path) -> Path:
        """Archive completed execution to history"""
        history_dir = vault_path / "ExecutionState" / "execution_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = history_dir / f"execution_{timestamp}_{self.execution_id}.json"

        with open(archive_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        # Remove active execution file
        active_file = vault_path / "ExecutionState" / "active_execution.json"
        if active_file.exists():
            active_file.unlink()

        return archive_file

    def update_progress(self):
        """Update progress metrics from tasks"""
        self.tasks_total = len(self.tasks)
        self.tasks_completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        self.tasks_failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        self.tasks_skipped = sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED)
        self.updated_at = datetime.now().isoformat()

    def get_completed_task_ids(self) -> set:
        """Get set of completed task IDs"""
        return {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}

    def get_pending_tasks(self) -> List[ExecutableTask]:
        """Get all pending tasks"""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_ready_tasks(self) -> List[ExecutableTask]:
        """Get tasks ready to execute (pending with met dependencies)"""
        completed_ids = self.get_completed_task_ids()
        return [t for t in self.tasks if t.can_execute(completed_ids)]

    def is_complete(self) -> bool:
        """Check if execution is complete (all tasks in terminal state)"""
        terminal_states = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(t.status in terminal_states for t in self.tasks)

    def mark_completed(self):
        """Mark execution as completed"""
        self.phase = ExecutionPhase.COMPLETED
        self.is_running = False
        self.completed_at = datetime.now().isoformat()
        self.update_progress()

    def mark_failed(self, reason: str):
        """Mark execution as failed"""
        self.phase = ExecutionPhase.FAILED
        self.is_running = False
        self.completed_at = datetime.now().isoformat()
        self.adjustments_made.append({
            "timestamp": datetime.now().isoformat(),
            "type": "execution_failed",
            "reason": reason
        })
        self.update_progress()

    def get_summary(self) -> str:
        """Get execution summary as markdown"""
        progress_pct = (self.tasks_completed / self.tasks_total * 100) if self.tasks_total > 0 else 0

        status_emoji = {
            ExecutionPhase.COMPLETED: "✅",
            ExecutionPhase.FAILED: "❌",
            ExecutionPhase.EXECUTING: "🔄",
        }.get(self.phase, "📋")

        summary = f"""# Execution Summary: {self.goal}

**Status:** {status_emoji} {self.phase.value.upper()}
**Progress:** {self.tasks_completed}/{self.tasks_total} tasks ({progress_pct:.1f}%)
**Iterations:** {self.iteration}/{self.max_iterations}

## Task Breakdown
- ✅ Completed: {self.tasks_completed}
- ❌ Failed: {self.tasks_failed}
- ⏭️ Skipped: {self.tasks_skipped}
- 📋 Pending: {len(self.get_pending_tasks())}

## Timeline
- Started: {self.created_at}
- Updated: {self.updated_at}
"""

        if self.completed_at:
            summary += f"- Completed: {self.completed_at}\n"

        if self.last_evaluation:
            summary += f"\n## Last Evaluation\n"
            summary += f"- On Track: {'✅ Yes' if self.last_evaluation.on_track else '❌ No'}\n"
            summary += f"- Confidence: {self.last_evaluation.confidence}\n"
            summary += f"- Should Continue: {'✅ Yes' if self.last_evaluation.should_continue else '❌ No'}\n"

        return summary
