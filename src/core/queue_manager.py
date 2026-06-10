"""
Offline queue system for graceful degradation.

Provides queue implementations for emails and tasks that fail due to
transient service unavailability.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaseQueue:
    """Base class for offline queues"""

    def __init__(self, queue_dir: Path, retention_days: int = 7):
        """
        Initialize queue.

        Args:
            queue_dir: Directory to store queue files
            retention_days: Days to retain items before expiration
        """
        self.queue_dir = queue_dir
        self.retention_days = retention_days
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def enqueue(self, item: dict):
        """
        Add item to queue.

        Args:
            item: Dictionary containing item data
        """
        timestamp = datetime.now().isoformat()
        filename = f"{timestamp.replace(':', '-')}.json"
        filepath = self.queue_dir / filename

        item['queued_at'] = timestamp
        filepath.write_text(json.dumps(item, indent=2))
        logger.info(f"Queued item to {filepath}")

    def dequeue_all(self) -> list:
        """
        Get all queued items.

        Returns:
            List of queued items with metadata
        """
        items = []
        for filepath in sorted(self.queue_dir.glob("*.json")):
            try:
                item = json.loads(filepath.read_text())
                item['queue_file'] = str(filepath)
                items.append(item)
            except Exception as e:
                logger.error(f"Failed to read queue item {filepath}: {e}")
        return items

    def remove(self, filepath: Path):
        """
        Remove processed item from queue.

        Args:
            filepath: Path to queue file
        """
        try:
            filepath = Path(filepath) if isinstance(filepath, str) else filepath
            filepath.unlink()
            logger.info(f"Removed processed item {filepath}")
        except Exception as e:
            logger.error(f"Failed to remove {filepath}: {e}")

    def cleanup_expired(self):
        """Remove items older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        for filepath in self.queue_dir.glob("*.json"):
            try:
                item = json.loads(filepath.read_text())
                queued_at = datetime.fromisoformat(item['queued_at'])

                if queued_at < cutoff:
                    filepath.unlink()
                    logger.info(f"Removed expired item {filepath}")
            except Exception as e:
                logger.error(f"Failed to cleanup {filepath}: {e}")


class EmailQueue(BaseQueue):
    """Queue for failed email sends"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern for email queue"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize email queue (only once)"""
        if not EmailQueue._initialized:
            vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'))
            queue_dir = vault_path / 'Queue' / 'emails'
            super().__init__(queue_dir, retention_days=7)
            EmailQueue._initialized = True


class TaskQueue(BaseQueue):
    """Queue for failed tasks"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern for task queue"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize task queue (only once)"""
        if not TaskQueue._initialized:
            vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'))
            queue_dir = vault_path / 'Queue' / 'tasks'
            super().__init__(queue_dir, retention_days=30)
            TaskQueue._initialized = True
