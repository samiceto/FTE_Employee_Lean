# Error Recovery & Graceful Degradation Implementation Plan

## Overview
Implement comprehensive error recovery and graceful degradation for the AI Employee autonomous system.

**Scope:** Full implementation - all phases
**Safety Rule:** Only invoice/expense operations in Odoo will never auto-retry

---

## Current State Analysis

### Existing Error Handling
- **Task-level retry**: ExecutionState model tracks attempts (max 3) with automatic retry
- **Skill retry**: BusinessAuditWatcher has `_execute_skill_with_retry()` with exponential backoff (2^n)
- **Observer restart**: Filesystem watcher auto-restarts on crash
- **Basic logging**: Structured logging to files and stdout

### Major Gaps
- No centralized retry decorators
- No rate limit handling (429 errors)
- No circuit breaker pattern
- No API timeouts for Odoo, Groq, Email
- No process-level watchdog for all watchers
- No dead letter queue
- No graceful degradation strategies

---

## Implementation Plan

### Phase 1: Error Classification System

**Create:** `src/core/errors.py`

Define error hierarchy:
```python
class TransientError(Exception):
    """Errors that may resolve on retry (network, rate limits, timeouts)"""
    pass

class NetworkTimeout(TransientError):
    pass

class RateLimitExceeded(TransientError):
    pass

class ServiceUnavailable(TransientError):
    pass

class AuthenticationError(Exception):
    """Authentication/authorization failures requiring human intervention"""
    pass

class TokenExpired(AuthenticationError):
    pass

class InvalidCredentials(AuthenticationError):
    pass

class PermissionDenied(AuthenticationError):
    pass

class LogicError(Exception):
    """Business logic errors requiring human review"""
    pass

class TaskValidationError(LogicError):
    pass

class PlanExecutionError(LogicError):
    pass

class DataError(Exception):
    """Data quality/corruption issues"""
    pass

class CorruptedFile(DataError):
    pass

class MissingField(DataError):
    pass

class ValidationError(DataError):
    pass

class SystemError(Exception):
    """System-level failures (disk, memory, process crashes)"""
    pass

class ProcessCrashed(SystemError):
    pass

class DiskFull(SystemError):
    pass

class MemoryExhausted(SystemError):
    pass
```

**Recovery Strategies:**
- **Transient** → Exponential backoff retry (auto-recover)
- **Authentication** → Alert human, pause operations
- **Logic** → Human review queue
- **Data** → Quarantine + alert
- **System** → Watchdog restart

---

### Phase 2: Retry Handler Decorator

**Create:** `src/core/retry_handler.py`

Implement `@with_retry` decorator:
```python
import time
import logging
from functools import wraps
from .errors import TransientError

logger = logging.getLogger(__name__)

def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1)
        max_delay: Maximum delay in seconds (default: 60)

    Only retries on TransientError exceptions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    if attempt == max_attempts - 1:
                        logger.error(f'{func.__name__} failed after {max_attempts} attempts: {e}')
                        raise

                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f'{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {e}. '
                        f'Retrying in {delay}s...'
                    )
                    time.sleep(delay)

        return wrapper
    return decorator
```

**Update existing code:**
- Replace `_execute_skill_with_retry()` in `src/watchers/business_audit_watcher.py` with decorator
- Apply to API calls in Groq, Odoo, Email clients

---

### Phase 3: Enhanced API Clients

#### 3.1 Groq LLM Client
**File:** `src/skills/base_skill.py:75-104`

**Changes to `_call_groq()` method:**
```python
from src.core.retry_handler import with_retry
from src.core.errors import NetworkTimeout, RateLimitExceeded, ServiceUnavailable

@with_retry(max_attempts=3, base_delay=1, max_delay=60)
def _call_groq(self, messages, temperature=0.7, max_tokens=2000):
    try:
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30  # ADD: 30 second timeout
        )
        return response
    except TimeoutError as e:
        raise NetworkTimeout(f"Groq API timeout: {e}")
    except Exception as e:
        if '429' in str(e) or 'rate_limit' in str(e).lower():
            raise RateLimitExceeded(f"Groq rate limit: {e}")
        elif 'unavailable' in str(e).lower():
            raise ServiceUnavailable(f"Groq unavailable: {e}")
        raise
```

**Fallback behavior:**
- When Groq unavailable, queue task to `ai_employee_vault/Queue/tasks/`
- Background worker retries every 5 minutes

#### 3.2 Odoo Client
**File:** `src/mcp_servers/odoo/odoo_mcp_server.py:63-90`

**CRITICAL: Payment Operation Safety**
```python
PAYMENT_OPERATIONS = {'create_invoice', 'record_expense', 'update_invoice'}

def is_payment_operation(self, operation_name: str) -> bool:
    """Check if operation involves financial transactions"""
    return operation_name in PAYMENT_OPERATIONS
```

**Enhance `__init__()` method:**
```python
import socket
from src.core.errors import NetworkTimeout, AuthenticationError

def __init__(self, url, db, username, password):
    self.url = url
    self.db = db
    self.username = username

    # ADD: Connection timeout
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(10)  # 10 second timeout

    try:
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.uid = self.common.authenticate(db, username, password, {})

        if not self.uid:
            raise AuthenticationError("Odoo authentication failed")

        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    finally:
        socket.setdefaulttimeout(old_timeout)
```

**Wrap operations with conditional retry:**
```python
from src.core.retry_handler import with_retry

def execute_operation(self, operation_name, *args):
    """Execute Odoo operation with conditional retry"""

    # NEVER auto-retry payment operations
    if self.is_payment_operation(operation_name):
        logger.warning(f"Payment operation {operation_name} - no auto-retry")
        return self._execute_once(operation_name, *args)

    # Safe operations can retry
    @with_retry(max_attempts=3)
    def _execute_with_retry():
        return self._execute_once(operation_name, *args)

    return _execute_with_retry()

def _execute_once(self, operation_name, *args):
    """Execute operation once without retry"""
    try:
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            operation_name, args
        )
    except socket.timeout:
        raise NetworkTimeout(f"Odoo operation {operation_name} timed out")
```

#### 3.3 Email Client
**File:** `src/mcp_servers/email/mcp_server_email.py:126-134`

**Add to `send_email()` method:**
```python
import smtplib
from src.core.retry_handler import with_retry
from src.core.errors import NetworkTimeout, ServiceUnavailable
from src.core.queue_manager import EmailQueue

@with_retry(max_attempts=3, base_delay=2, max_delay=30)
def _send_email_with_smtp(self, receiver, subject, body, attachments=None):
    """Send email with timeout and retry"""
    try:
        smtp = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
        # ... existing SMTP logic
        smtp.quit()
    except smtplib.SMTPException as e:
        raise ServiceUnavailable(f"SMTP error: {e}")
    except socket.timeout:
        raise NetworkTimeout("SMTP timeout")

def send_email(self, receiver, subject, body, attachments=None):
    """Send email with graceful degradation to queue"""
    try:
        return self._send_email_with_smtp(receiver, subject, body, attachments)
    except (NetworkTimeout, ServiceUnavailable) as e:
        # Fallback: Queue locally when Gmail unavailable
        logger.warning(f"Gmail unavailable, queueing email: {e}")
        EmailQueue.enqueue({
            'receiver': receiver,
            'subject': subject,
            'body': body,
            'attachments': attachments,
            'timestamp': time.time()
        })
        return {'success': False, 'queued': True, 'error': str(e)}
```

---

### Phase 4: Graceful Degradation

**Create:** `src/core/queue_manager.py`

Implement offline queue system:
```python
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BaseQueue:
    """Base class for offline queues"""

    def __init__(self, queue_dir: Path, retention_days: int = 7):
        self.queue_dir = queue_dir
        self.retention_days = retention_days
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def enqueue(self, item: dict):
        """Add item to queue"""
        timestamp = datetime.now().isoformat()
        filename = f"{timestamp.replace(':', '-')}.json"
        filepath = self.queue_dir / filename

        item['queued_at'] = timestamp
        filepath.write_text(json.dumps(item, indent=2))
        logger.info(f"Queued item to {filepath}")

    def dequeue_all(self) -> list:
        """Get all queued items"""
        items = []
        for filepath in sorted(self.queue_dir.glob("*.json")):
            try:
                item = json.loads(filepath.read_text())
                item['queue_file'] = filepath
                items.append(item)
            except Exception as e:
                logger.error(f"Failed to read queue item {filepath}: {e}")
        return items

    def remove(self, filepath: Path):
        """Remove processed item from queue"""
        try:
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

    def __new__(cls):
        if cls._instance is None:
            vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'))
            queue_dir = vault_path / 'Queue' / 'emails'
            cls._instance = super().__new__(cls)
            super(EmailQueue, cls._instance).__init__(queue_dir, retention_days=7)
        return cls._instance


class TaskQueue(BaseQueue):
    """Queue for failed tasks"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'))
            queue_dir = vault_path / 'Queue' / 'tasks'
            cls._instance = super().__new__(cls)
            super(TaskQueue, cls._instance).__init__(queue_dir, retention_days=30)
        return cls._instance
```

**Component Health Tracking:**

**Create:** `src/core/health_monitor.py`

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

class ComponentHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"

@dataclass
class ComponentStatus:
    name: str
    health: ComponentHealth
    last_check: datetime
    error_count: int = 0
    last_error: str = ""

    def to_dict(self):
        return {
            'name': self.name,
            'health': self.health.value,
            'last_check': self.last_check.isoformat(),
            'error_count': self.error_count,
            'last_error': self.last_error
        }

class HealthMonitor:
    """Tracks health status of all components"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.components = {}
            cls._instance.status_file = Path('/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault/.component_health.json')
        return cls._instance

    def update_status(self, component: str, health: ComponentHealth, error: str = ""):
        """Update component health status"""
        self.components[component] = ComponentStatus(
            name=component,
            health=health,
            last_check=datetime.now(),
            error_count=self.components.get(component, ComponentStatus(component, health, datetime.now())).error_count + (1 if error else 0),
            last_error=error
        )
        self._persist()

    def get_status(self, component: str) -> ComponentStatus:
        """Get component status"""
        return self.components.get(component, ComponentStatus(component, ComponentHealth.HEALTHY, datetime.now()))

    def is_healthy(self, component: str) -> bool:
        """Check if component is healthy"""
        status = self.get_status(component)
        return status.health == ComponentHealth.HEALTHY

    def _persist(self):
        """Save status to disk"""
        data = {k: v.to_dict() for k, v in self.components.items()}
        self.status_file.write_text(json.dumps(data, indent=2))
```

**Graceful Degradation Strategies:**
- **Gmail API down** → Queue emails locally, retry every 5 minutes
- **Groq API unavailable** → Queue tasks, retry every 5 minutes
- **Odoo API timeout** → Alert human, no auto-retry for payments
- **Vault locked** → Write to `/tmp/vault_fallback/`, sync when available

---

### Phase 5: Watchdog Process

**Create:** `src/core/watchdog.py`

Monitor and restart critical processes:
```python
import subprocess
import time
from pathlib import Path
import logging
import signal
from src.core.notifier import Notifier

logger = logging.getLogger(__name__)

PROCESSES = {
    'ralph_wiggum_loop': {
        'command': 'python -m src.orchestrator.ralph_wiggum_loop',
        'pid_file': '/tmp/ralph_wiggum_loop.pid',
        'max_restarts_per_hour': 5
    },
    'gmail_watcher': {
        'command': 'python -m src.watchers.gmail_watcher',
        'pid_file': '/tmp/gmail_watcher.pid',
        'max_restarts_per_hour': 5
    },
    'filesystem_watcher': {
        'command': 'python -m src.watcher.filesystem_watcher_daemon',
        'pid_file': '/tmp/filesystem_watcher.pid',
        'max_restarts_per_hour': 5
    },
    'business_audit_watcher': {
        'command': 'python -m src.watchers.business_audit_watcher',
        'pid_file': '/tmp/business_audit_watcher.pid',
        'max_restarts_per_hour': 3
    }
}

class ProcessWatchdog:
    """Monitor and restart critical processes"""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.restart_history = {}  # {process_name: [timestamp1, timestamp2, ...]}
        self.notifier = Notifier()
        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def is_process_running(self, pid_file: Path) -> bool:
        """Check if process is running via PID file"""
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ValueError, OSError):
            return False

    def can_restart(self, process_name: str, max_restarts: int) -> bool:
        """Check if process can be restarted (within rate limit)"""
        now = time.time()
        hour_ago = now - 3600

        # Clean old restart history
        if process_name in self.restart_history:
            self.restart_history[process_name] = [
                ts for ts in self.restart_history[process_name] if ts > hour_ago
            ]
        else:
            self.restart_history[process_name] = []

        return len(self.restart_history[process_name]) < max_restarts

    def start_process(self, process_name: str, config: dict):
        """Start a process and track its PID"""
        logger.info(f"Starting {process_name}...")

        proc = subprocess.Popen(
            config['command'].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        pid_file = Path(config['pid_file'])
        pid_file.write_text(str(proc.pid))

        # Track restart
        self.restart_history.setdefault(process_name, []).append(time.time())

        logger.info(f"{process_name} started with PID {proc.pid}")
        return proc

    def check_and_restart(self):
        """Check all processes and restart if needed"""
        for name, config in PROCESSES.items():
            pid_file = Path(config['pid_file'])

            if not self.is_process_running(pid_file):
                logger.warning(f"{name} not running, attempting restart...")

                if self.can_restart(name, config['max_restarts_per_hour']):
                    self.start_process(name, config)
                    self.notifier.alert(
                        level='WARNING',
                        component=name,
                        message=f"{name} was restarted by watchdog"
                    )
                else:
                    logger.critical(f"{name} exceeded max restarts, manual intervention required")
                    self.notifier.alert(
                        level='CRITICAL',
                        component=name,
                        message=f"{name} exceeded max restarts per hour, manual intervention required"
                    )

    def run(self):
        """Main watchdog loop"""
        logger.info("Watchdog process started")

        while self.running:
            try:
                self.check_and_restart()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Watchdog error: {e}", exc_info=True)
                time.sleep(5)  # Short sleep on error

    def _shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info("Watchdog shutting down...")
        self.running = False

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/mnt/d/FTE_Employee/hackathon_zero/logs/watchdog.log'),
            logging.StreamHandler()
        ]
    )

    watchdog = ProcessWatchdog(check_interval=60)
    watchdog.run()
```

**Update PM2 Configuration:**

**File:** `ecosystem.config.js`

Add watchdog process:
```javascript
{
  name: 'watchdog',
  script: 'python',
  args: '-m src.core.watchdog',
  cwd: '/mnt/d/FTE_Employee/hackathon_zero',
  interpreter: 'none',
  autorestart: true,
  max_restarts: 10,
  restart_delay: 5000,
  error_file: 'logs/watchdog-error.log',
  out_file: 'logs/watchdog-out.log',
  log_date_format: 'YYYY-MM-DD HH:mm:ss'
}
```

---

### Phase 6: Dead Letter Queue

**Create:** `src/core/dead_letter_queue.py`

```python
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import traceback

logger = logging.getLogger(__name__)

class DeadLetterQueue:
    """Store failed tasks for human review"""

    def __init__(self, vault_path: Path):
        self.dlq_dir = vault_path / 'Queue' / 'dead_letter'
        self.review_dir = vault_path / 'Need_Action' / 'failed_tasks'
        self.dlq_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def add_failed_task(self, task, error_message: str, stack_trace: str = None):
        """Add failed task to dead letter queue"""
        timestamp = datetime.now().isoformat()
        filename = f"FAILED_{task.id}_{timestamp.replace(':', '-')}.json"
        filepath = self.dlq_dir / filename

        dlq_item = {
            'task_id': task.id,
            'action': task.action,
            'skill_name': task.skill_name,
            'skill_input': task.skill_input,
            'attempts': task.attempts,
            'max_attempts': task.max_attempts,
            'error_message': error_message,
            'stack_trace': stack_trace or traceback.format_exc(),
            'failed_at': timestamp,
            'metadata': task.metadata
        }

        filepath.write_text(json.dumps(dlq_item, indent=2))
        logger.error(f"Task {task.id} moved to dead letter queue: {filepath}")

        # Create human review task
        self._create_review_task(dlq_item, filepath)

    def _create_review_task(self, dlq_item, dlq_filepath: Path):
        """Create task in Need_Action for human review"""
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
        """Archive items older than retention period"""
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
```

**Update ExecutionState:**

**File:** `src/models/execution_state.py:87-97`

Modify `mark_failed()` method:
```python
from src.core.dead_letter_queue import DeadLetterQueue

def mark_failed(self, error_message: str, vault_path: Path = None):
    """Mark task as failed, retry if attempts remain, else send to DLQ"""
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
            dlq = DeadLetterQueue(vault_path)
            dlq.add_failed_task(self, error_message)
```

---

### Phase 7: Notification System

**Create:** `src/core/notifier.py`

```python
import logging
from datetime import datetime, timedelta
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

logger = logging.getLogger(__name__)

class AlertLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class Notifier:
    """Alert system for errors and system events"""

    def __init__(self):
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL_ID')
        self.slack_client = WebClient(token=self.slack_token) if self.slack_token else None

        self.vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault'))
        self.dashboard_path = self.vault_path / 'Dashboard.md'

        # Rate limiting: max 1 alert per component per 5 minutes
        self.alert_history = {}  # {component: last_alert_time}
        self.rate_limit_seconds = 300

    def can_alert(self, component: str) -> bool:
        """Check if component can send alert (rate limiting)"""
        now = datetime.now()

        if component in self.alert_history:
            last_alert = self.alert_history[component]
            if (now - last_alert).total_seconds() < self.rate_limit_seconds:
                return False

        return True

    def alert(self, level: str, component: str, message: str):
        """Send alert through all channels"""
        if not self.can_alert(component):
            logger.debug(f"Alert for {component} rate-limited, skipping")
            return

        self.alert_history[component] = datetime.now()

        # Log
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        log_method(f"[{level}] {component}: {message}")

        # Slack
        if self.slack_client and level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self._send_slack(level, component, message)

        # Dashboard
        self._update_dashboard(level, component, message)

        # Email (fallback for CRITICAL)
        if level == AlertLevel.CRITICAL and not self.slack_client:
            self._send_email_alert(component, message)

    def _send_slack(self, level: str, component: str, message: str):
        """Send Slack notification"""
        try:
            emoji = {
                AlertLevel.INFO: ":information_source:",
                AlertLevel.WARNING: ":warning:",
                AlertLevel.CRITICAL: ":rotating_light:"
            }.get(level, ":bell:")

            self.slack_client.chat_postMessage(
                channel=self.slack_channel,
                text=f"{emoji} *{level}*: {component}\n{message}"
            )
            logger.info(f"Slack alert sent for {component}")
        except SlackApiError as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _update_dashboard(self, level: str, component: str, message: str):
        """Update Dashboard.md with alert"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_line = f"- **[{timestamp}]** [{level}] {component}: {message}\n"

            if self.dashboard_path.exists():
                content = self.dashboard_path.read_text()

                # Add to alerts section
                if "## Recent Alerts" in content:
                    parts = content.split("## Recent Alerts")
                    content = parts[0] + "## Recent Alerts\n\n" + alert_line + parts[1].lstrip()
                else:
                    content += f"\n\n## Recent Alerts\n\n{alert_line}"

                self.dashboard_path.write_text(content)
            else:
                self.dashboard_path.write_text(f"## Recent Alerts\n\n{alert_line}")

            logger.info(f"Dashboard updated with {level} alert for {component}")
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def _send_email_alert(self, component: str, message: str):
        """Send email alert (fallback for critical issues)"""
        try:
            from src.mcp_servers.email.mcp_server_email import send_email

            send_email(
                receiver=[os.getenv('ADMIN_EMAIL', 'admin@example.com')],
                subject=f"CRITICAL: {component} Failure",
                body=f"Critical failure in {component}:\n\n{message}"
            )
            logger.info(f"Email alert sent for {component}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
```

---

## File Structure

```
/mnt/d/FTE_Employee/hackathon_zero/
├── src/
│   ├── core/                          # NEW
│   │   ├── __init__.py
│   │   ├── errors.py                  # Error hierarchy
│   │   ├── retry_handler.py           # @with_retry decorator
│   │   ├── queue_manager.py           # Offline queues (EmailQueue, TaskQueue)
│   │   ├── health_monitor.py          # Component health tracking
│   │   ├── dead_letter_queue.py       # Failed task storage
│   │   ├── notifier.py                # Alert system (Slack, Dashboard, Email)
│   │   └── watchdog.py                # Process monitor daemon
│   ├── skills/base_skill.py           # MODIFY: Add timeout to Groq, @with_retry
│   ├── models/execution_state.py      # MODIFY: Dead letter integration
│   ├── mcp_servers/
│   │   ├── odoo/odoo_mcp_server.py    # MODIFY: Timeout, conditional retry
│   │   └── email/mcp_server_email.py  # MODIFY: Timeout, queue fallback
│   └── watchers/
│       └── business_audit_watcher.py  # MODIFY: Use @with_retry decorator
├── ai_employee_vault/
│   └── Queue/                         # NEW
│       ├── emails/                    # Queued emails
│       ├── tasks/                     # Queued tasks
│       └── dead_letter/               # Failed tasks
│           └── archive/               # Expired items (30 days+)
├── ecosystem.config.js                # MODIFY: Add watchdog
├── logs/
│   └── watchdog.log                   # NEW
└── error_recovery_and_graceful_degradation_plan.md  # This file
```

---

## Critical Files to Modify

1. `src/skills/base_skill.py:75-104`
   - Add timeout to Groq client
   - Wrap `_call_groq()` with retry logic

2. `src/mcp_servers/odoo/odoo_mcp_server.py:63-90`
   - Add connection timeout
   - Add payment operation check (no auto-retry)

3. `src/mcp_servers/email/mcp_server_email.py:126-134`
   - Add SMTP timeout
   - Add queue fallback

4. `src/models/execution_state.py:87-97`
   - Integrate dead letter queue

5. `src/watchers/business_audit_watcher.py:300-328`
   - Replace custom retry with decorator

6. `ecosystem.config.js`
   - Add watchdog process

---

## Implementation Order

### Week 1: Foundation (Days 1-2)
1. ✅ Create `src/core/` directory
2. ✅ Create `src/core/errors.py` - Error hierarchy
3. ✅ Create `src/core/retry_handler.py` - `@with_retry` decorator
4. ✅ Add unit tests for retry logic (`tests/test_retry.py`)

### Week 2: API Enhancements (Days 3-5)
5. ✅ Update `src/skills/base_skill.py` - Groq timeout + retry
6. ✅ Update `src/mcp_servers/odoo/odoo_mcp_server.py` - Timeout, conditional retry
7. ✅ Update `src/mcp_servers/email/mcp_server_email.py` - Timeout, queue fallback
8. ✅ Update `src/watchers/business_audit_watcher.py` - Replace custom retry with decorator

### Week 3: Queue & Recovery (Days 6-8)
9. ✅ Create `src/core/queue_manager.py` - EmailQueue, TaskQueue
10. ✅ Create `src/core/health_monitor.py` - Component health tracking
11. ✅ Create `src/core/dead_letter_queue.py` - Failed task handling
12. ✅ Update `src/models/execution_state.py` - Integrate dead letter queue
13. ✅ Create `ai_employee_vault/Queue/` directories

### Week 4: Monitoring (Days 9-10)
14. ✅ Create `src/core/watchdog.py` - Process monitoring daemon
15. ✅ Create `src/core/notifier.py` - Alert system
16. ✅ Update `ecosystem.config.js` - Add watchdog process
17. ✅ Update `Dashboard.md` template with health section

---

## Testing Strategy

### Unit Tests

**Create:** `tests/test_retry.py`
```python
import pytest
import time
from src.core.retry_handler import with_retry
from src.core.errors import TransientError

def test_retry_success_on_first_attempt():
    call_count = 0

    @with_retry(max_attempts=3)
    def succeeds_immediately():
        nonlocal call_count
        call_count += 1
        return "success"

    result = succeeds_immediately()
    assert result == "success"
    assert call_count == 1

def test_retry_success_on_second_attempt():
    call_count = 0

    @with_retry(max_attempts=3)
    def succeeds_on_retry():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise TransientError("Temporary failure")
        return "success"

    result = succeeds_on_retry()
    assert result == "success"
    assert call_count == 2

def test_retry_exhaustion():
    @with_retry(max_attempts=3)
    def always_fails():
        raise TransientError("Always fails")

    with pytest.raises(TransientError):
        always_fails()

def test_exponential_backoff():
    @with_retry(max_attempts=3, base_delay=1, max_delay=10)
    def track_delays():
        raise TransientError("Test")

    start = time.time()
    with pytest.raises(TransientError):
        track_delays()
    elapsed = time.time() - start

    # Should have delays: 1s + 2s = 3s minimum
    assert elapsed >= 3
```

**Create:** `tests/test_queue.py`
```python
import pytest
from pathlib import Path
from src.core.queue_manager import EmailQueue, TaskQueue

def test_email_queue_enqueue_dequeue(tmp_path):
    queue = EmailQueue()
    queue.queue_dir = tmp_path

    queue.enqueue({
        'receiver': 'test@example.com',
        'subject': 'Test',
        'body': 'Hello'
    })

    items = queue.dequeue_all()
    assert len(items) == 1
    assert items[0]['receiver'] == 'test@example.com'

def test_queue_cleanup_expired(tmp_path):
    queue = EmailQueue()
    queue.queue_dir = tmp_path
    queue.retention_days = 0  # Expire immediately

    queue.enqueue({'test': 'data'})
    queue.cleanup_expired()

    items = queue.dequeue_all()
    assert len(items) == 0
```

### Integration Tests

**Create:** `tests/test_api_failures.py`
```python
import pytest
from unittest.mock import patch, Mock
from src.skills.base_skill import BaseSkill
from src.core.errors import NetworkTimeout, RateLimitExceeded

def test_groq_timeout_retry():
    """Test Groq API timeout triggers retry"""

    call_count = 0

    with patch('groq.Groq') as mock_groq:
        mock_client = Mock()

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return Mock(choices=[Mock(message=Mock(content="Success"))])

        mock_client.chat.completions.create.side_effect = side_effect
        mock_groq.return_value = mock_client

        skill = BaseSkill()
        result = skill._call_groq([{"role": "user", "content": "test"}])

        assert call_count == 2  # First failed, second succeeded

def test_groq_rate_limit():
    """Test Groq rate limit detection"""

    with patch('groq.Groq') as mock_groq:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("429 rate limit exceeded")
        mock_groq.return_value = mock_client

        skill = BaseSkill()

        with pytest.raises(RateLimitExceeded):
            skill._call_groq([{"role": "user", "content": "test"}])
```

### Chaos Testing

**Create:** `tests/chaos_test.py`
```python
import subprocess
import time
import os
import signal
from pathlib import Path

def test_watchdog_restart():
    """Kill a process and verify watchdog restarts it"""

    # Start watchdog
    watchdog_proc = subprocess.Popen(['python', '-m', 'src.core.watchdog'])
    time.sleep(5)  # Let watchdog start monitoring

    # Start a monitored process
    pid_file = Path('/tmp/gmail_watcher.pid')
    if pid_file.exists():
        pid = int(pid_file.read_text())

        # Kill the process
        os.kill(pid, signal.SIGKILL)

        # Wait for watchdog to detect and restart
        time.sleep(65)  # Watchdog checks every 60s

        # Verify process restarted
        assert pid_file.exists()
        new_pid = int(pid_file.read_text())
        assert new_pid != pid  # Different PID means it restarted

    # Cleanup
    watchdog_proc.terminate()
```

---

## Rollout Strategy

### Phase A: Foundation (Low Risk) - Days 1-2
**Deploy:**
1. Create `src/core/` directory structure
2. Add error classes (`errors.py`)
3. Add retry decorator (`retry_handler.py`)
4. Run unit tests

**Validation:**
- ✅ Import errors in Python REPL: `from src.core.errors import TransientError`
- ✅ Test decorator: `@with_retry()` works in isolation
- ✅ All unit tests pass

**Rollback:** Delete `src/core/` (no impact on running system)

---

### Phase B: API Client Updates (Medium Risk) - Days 3-5

**Deploy (one at a time):**
1. **Day 3**: Update Groq client (`base_skill.py`)
   - Add timeout=30
   - Add `@with_retry` decorator
   - Test with sample skill execution

2. **Day 4**: Update Email client (`mcp_server_email.py`)
   - Add timeout=15
   - Add queue fallback (create queue first)
   - Test by sending test email

3. **Day 5**: Update Odoo client (`odoo_mcp_server.py`) - **CRITICAL**
   - Add timeout=10
   - Add payment operation check
   - **Thoroughly test** on staging environment first
   - Verify invoices/expenses do NOT auto-retry

**Validation:**
- ✅ Groq: Simulate timeout (disconnect network), verify retry works
- ✅ Email: Disconnect Gmail, verify email queues locally
- ✅ Odoo: Test read operations retry, payment operations fail fast

**Rollback:** Git revert each file individually if issues arise

---

### Phase C: Queue & Recovery (Medium Risk) - Days 6-8

**Deploy:**
1. Create queue directories (`ai_employee_vault/Queue/`)
2. Deploy queue manager (`queue_manager.py`)
3. Deploy health monitor (`health_monitor.py`)
4. Deploy dead letter queue (`dead_letter_queue.py`)
5. Update `ExecutionState` to use DLQ

**Validation:**
- ✅ Queue: Manually enqueue email, verify file created
- ✅ Health: Update component status, verify persisted
- ✅ DLQ: Force task failure, verify review task created in `Need_Action/`

**Rollback:** Delete queue directories, revert `execution_state.py`

---

### Phase D: Monitoring (Low Risk) - Days 9-10

**Deploy:**
1. Deploy notifier (`notifier.py`)
2. Deploy watchdog (`watchdog.py`)
3. Update PM2 config (`ecosystem.config.js`)
4. Restart PM2: `pm2 restart ecosystem.config.js`

**Validation:**
- ✅ Notifier: Trigger test alert, verify Slack message + Dashboard update
- ✅ Watchdog: Kill a watcher process, verify restart within 60s
- ✅ PM2: Verify watchdog process running in `pm2 list`

**Rollback:** Remove watchdog from PM2 config, restart PM2

---

### Phase E: Monitoring & Tuning - Week 2+

**Monitor for 1 week:**
- Check `logs/watchdog.log` daily
- Review Slack alerts
- Verify queue sizes (`Queue/emails/`, `Queue/tasks/`)
- Check dead letter queue for patterns

**Tune parameters:**
- Adjust timeouts if too aggressive
- Adjust max_restarts if too restrictive
- Adjust retry delays based on real-world behavior

---

## Verification Checklist

### Error Recovery
- [ ] Transient errors retry with exponential backoff
- [ ] Max 3 attempts before failure
- [ ] Delays: 1s, 2s, 4s (capped at 60s)
- [ ] Non-transient errors fail immediately

### Graceful Degradation
- [ ] Gmail API down → Emails queued locally in `Queue/emails/`
- [ ] Groq API down → Tasks queued in `Queue/tasks/`
- [ ] Odoo timeout → **Invoices/expenses do NOT auto-retry**
- [ ] Odoo timeout → Read operations retry up to 3 times
- [ ] Vault locked → Falls back to `/tmp/vault_fallback/`

### Watchdog
- [ ] Detects crashed processes within 60 seconds
- [ ] Auto-restarts with PID tracking
- [ ] Sends Slack alert on restart
- [ ] Max 5 restarts per hour per process
- [ ] Critical alert if max restarts exceeded

### Dead Letter Queue
- [ ] Failed tasks stored in `Queue/dead_letter/`
- [ ] Includes: task details, error, stack trace, attempts
- [ ] Human review task created in `Need_Action/failed_tasks/`
- [ ] 30-day expiration, moved to archive

### Notifications
- [ ] Slack alerts for WARNING and CRITICAL
- [ ] Dashboard.md updated with all alerts
- [ ] Rate limiting: max 1 alert per component per 5 minutes
- [ ] Email fallback for CRITICAL if Slack unavailable

---

## Success Metrics

**Target Metrics (after 1 month):**
- **MTTR (Mean Time To Recovery):** < 2 minutes for process crashes
- **Error Recovery Rate:** > 95% of transient errors auto-recover
- **False Alert Rate:** < 5% of Slack alerts are false positives
- **Queue Processing:** 99% of queued items processed within 1 hour
- **Payment Safety:** 0% accidental payment retries (CRITICAL)

**Tracking:**
- Log metrics daily to `logs/metrics.log`
- Weekly review in CEO briefing
- Alert if any metric degrades

---

## Dependencies

**Required:**
- Python 3.12+
- Existing: Groq SDK, Google Gmail API, Odoo xmlrpc, Slack SDK
- PM2 (already configured in `ecosystem.config.js`)

**New Libraries:**
- **None** - Using Python standard library for all new components

**Configuration:**
Add to `.env`:
```bash
# Error Recovery
WATCHDOG_CHECK_INTERVAL=60
QUEUE_RETENTION_DAYS=7
DLQ_RETENTION_DAYS=30

# Timeouts (seconds)
GROQ_TIMEOUT=30
ODOO_TIMEOUT=10
EMAIL_TIMEOUT=15

# Alerts
ADMIN_EMAIL=admin@example.com
```

---

## Risks & Mitigations

**Risk 1:** Odoo payment retry could double-charge customers
- **Mitigation:** Explicit `is_payment_operation()` check, **never** auto-retry invoices/expenses
- **Testing:** Thoroughly test on staging, verify no payment retries

**Risk 2:** Queue grows unbounded
- **Mitigation:** 7-day retention for emails, 30-day for dead letter, automatic cleanup

**Risk 3:** Watchdog creates restart loop (thrashing)
- **Mitigation:** Max 5 restarts per hour, exponential backoff, critical alert

**Risk 4:** Groq timeout too aggressive (false positives)
- **Mitigation:** Start with 30s, monitor logs, increase if needed

**Risk 5:** Breaking existing watchers during API updates
- **Mitigation:** Deploy Phase A first (new code only), test before modifying existing

**Risk 6:** Dead letter queue fills disk
- **Mitigation:** 30-day expiration, automatic archival, monitor disk usage

---

## Post-Deployment

**Week 1:**
- Monitor `logs/watchdog.log` daily
- Check Slack alerts for patterns
- Review queue sizes
- Verify no payment retries in Odoo logs

**Week 2:**
- Analyze error recovery rate
- Tune timeout values if needed
- Adjust retry delays based on real-world data

**Month 1:**
- Calculate success metrics (MTTR, recovery rate, etc.)
- Review dead letter queue for patterns
- Optimize based on findings
- Document lessons learned

---

## Next Steps

1. **Read and approve this plan** 📋
2. **Implementation begins** with Phase A (Foundation)
3. **Deploy incrementally** following rollout strategy
4. **Monitor closely** during first week
5. **Iterate and improve** based on real-world data

---

*Plan created: 2026-01-21*
*Implementation scope: Full - all phases*
*Estimated duration: 10 days + 1 week monitoring*
