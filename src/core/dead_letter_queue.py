"""
Dead Letter Queue - Store failed tasks for human review.

When tasks fail after exhausting all retry attempts, they are moved to
the dead letter queue and a human review task is created.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import traceback

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """Store failed tasks for human review"""

    def __init__(self, vault_path: Path):
        """
        Initialize dead letter queue.

        Args:
            vault_path: Path to AI employee vault
        """
        self.dlq_dir = vault_path / 'Queue' / 'dead_letter'
        self.review_dir = vault_path / 'Need_Action' / 'failed_tasks'
        self.dlq_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def add_failed_task(self, task, error_message: str, stack_trace: str = None):
        """
        Add failed task to dead letter queue.

        Args:
            task: Task object with id, action, skill_name, etc.
            error_message: Error message describing the failure
            stack_trace: Optional stack trace
        """
        timestamp = datetime.now().isoformat()
        filename = f"FAILED_{task.id}_{timestamp.replace(':', '-')}.json"
        filepath = self.dlq_dir / filename

        # Get task attributes safely
        task_id = getattr(task, 'id', 'unknown')
        action = getattr(task, 'action', 'unknown')
        skill_name = getattr(task, 'skill_name', 'unknown')
        skill_input = getattr(task, 'skill_input', {})
        attempts = getattr(task, 'attempts', 0)
        max_attempts = getattr(task, 'max_attempts', 3)
        metadata = getattr(task, 'metadata', {})

        dlq_item = {
            'task_id': task_id,
            'action': action,
            'skill_name': skill_name,
            'skill_input': skill_input,
            'attempts': attempts,
            'max_attempts': max_attempts,
            'error_message': error_message,
            'stack_trace': stack_trace or traceback.format_exc(),
            'failed_at': timestamp,
            'metadata': metadata
        }

        filepath.write_text(json.dumps(dlq_item, indent=2))
        logger.error(f"Task {task_id} moved to dead letter queue: {filepath}")

        # Create human review task
        self._create_review_task(dlq_item, filepath)

    def _create_review_task(self, dlq_item, dlq_filepath: Path):
        """
        Create task in Need_Action for human review.

        Args:
            dlq_item: Dead letter queue item data
            dlq_filepath: Path to DLQ file
        """
        review_filename = f"REVIEW_FAILED_TASK_{dlq_item['task_id']}.md"
        review_filepath = self.review_dir / review_filename

        content = f"""# Failed Task Review Required

**Task ID:** {dlq_item['task_id']}
**Failed At:** {dlq_item['failed_at']}
**Attempts:** {dlq_item['attempts']}/{dlq_item['max_attempts']}

## Task Details

**Action:** {dlq_item['action']}
**Skill:** {dlq_item['skill_name']}

**Input:**
```json
{json.dumps(dlq_item['skill_input'], indent=2)}
```

## Error

**Message:** {dlq_item['error_message']}

**Stack Trace:**
```
{dlq_item['stack_trace']}
```

## Actions Required

1. **Investigate** the error cause
2. **Fix** the underlying issue (code bug, data problem, config issue)
3. **Decide** whether to:
   - Retry the task manually
   - Skip the task
   - Modify and retry with different parameters

## Dead Letter Queue File

`{dlq_filepath}`

To retry after fixing:
1. Delete this review file
2. Delete the DLQ file or move it to archive
3. The system will automatically retry on next iteration
"""

        review_filepath.write_text(content)
        logger.info(f"Created review task: {review_filepath}")

    def cleanup_expired(self, days: int = 30):
        """
        Archive items older than retention period.

        Args:
            days: Number of days to retain items
        """
        archive_dir = self.dlq_dir / 'archive'
        archive_dir.mkdir(exist_ok=True)

        cutoff = datetime.now() - timedelta(days=days)

        for filepath in self.dlq_dir.glob("FAILED_*.json"):
            try:
                item = json.loads(filepath.read_text())
                failed_at = datetime.fromisoformat(item['failed_at'])

                if failed_at < cutoff:
                    archive_path = archive_dir / filepath.name
                    filepath.rename(archive_path)
                    logger.info(f"Archived expired DLQ item: {filepath} -> {archive_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup {filepath}: {e}")
