"""
Unit tests for queue manager.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.core.queue_manager import BaseQueue, EmailQueue, TaskQueue


def test_base_queue_enqueue_dequeue(tmp_path):
    """Test basic enqueue and dequeue operations"""
    queue = BaseQueue(tmp_path, retention_days=7)

    # Enqueue an item
    queue.enqueue({
        'receiver': 'test@example.com',
        'subject': 'Test',
        'body': 'Hello'
    })

    # Dequeue all items
    items = queue.dequeue_all()
    assert len(items) == 1
    assert items[0]['receiver'] == 'test@example.com'
    assert 'queued_at' in items[0]


def test_queue_remove(tmp_path):
    """Test removing items from queue"""
    queue = BaseQueue(tmp_path, retention_days=7)

    # Enqueue two items
    queue.enqueue({'test': 'data1'})
    queue.enqueue({'test': 'data2'})

    # Get all items
    items = queue.dequeue_all()
    assert len(items) == 2

    # Remove first item
    queue.remove(Path(items[0]['queue_file']))

    # Should have one item left
    items = queue.dequeue_all()
    assert len(items) == 1
    assert items[0]['test'] == 'data2'


def test_queue_cleanup_expired(tmp_path):
    """Test cleanup of expired items"""
    queue = BaseQueue(tmp_path, retention_days=1)

    # Create an old item (2 days ago)
    old_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
    old_file = tmp_path / f"{old_timestamp.replace(':', '-')}.json"
    old_file.write_text(json.dumps({'queued_at': old_timestamp, 'test': 'old'}))

    # Create a new item (now)
    queue.enqueue({'test': 'new'})

    # Before cleanup, should have 2 items
    items = queue.dequeue_all()
    assert len(items) == 2

    # Cleanup expired
    queue.cleanup_expired()

    # After cleanup, should have 1 item (the new one)
    items = queue.dequeue_all()
    assert len(items) == 1
    assert items[0]['test'] == 'new'


def test_email_queue_singleton():
    """Test that EmailQueue is a singleton"""
    queue1 = EmailQueue()
    queue2 = EmailQueue()
    assert queue1 is queue2


def test_task_queue_singleton():
    """Test that TaskQueue is a singleton"""
    queue1 = TaskQueue()
    queue2 = TaskQueue()
    assert queue1 is queue2


def test_queue_handles_corrupted_files(tmp_path):
    """Test that queue handles corrupted JSON files gracefully"""
    queue = BaseQueue(tmp_path, retention_days=7)

    # Create a corrupted file
    corrupted_file = tmp_path / "corrupted.json"
    corrupted_file.write_text("not valid json {{{")

    # Should not crash, just skip the corrupted file
    items = queue.dequeue_all()
    assert len(items) == 0


def test_queue_preserves_order(tmp_path):
    """Test that queue preserves FIFO order"""
    queue = BaseQueue(tmp_path, retention_days=7)

    # Enqueue items in order
    for i in range(5):
        queue.enqueue({'order': i})

    # Dequeue should return in same order
    items = queue.dequeue_all()
    assert len(items) == 5
    for i, item in enumerate(items):
        assert item['order'] == i
