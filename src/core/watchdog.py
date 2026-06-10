#!/usr/bin/env python3
"""
Watchdog Process - Monitor and restart critical system processes.

Monitors all critical watchers and loops, automatically restarting them
if they crash, with rate limiting to prevent restart loops.
"""

import subprocess
import time
import os
from pathlib import Path
import logging
import signal

logger = logging.getLogger(__name__)

# Process configurations
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
        """
        Initialize watchdog.

        Args:
            check_interval: Seconds between process checks
        """
        self.check_interval = check_interval
        self.restart_history = {}  # {process_name: [timestamp1, timestamp2, ...]}
        self.running = True

        # Import notifier here to avoid circular imports
        try:
            from src.core.notifier import Notifier
            self.notifier = Notifier()
        except Exception as e:
            logger.warning(f"Failed to initialize notifier: {e}")
            self.notifier = None

        # Register signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def is_process_running(self, pid_file: Path) -> bool:
        """
        Check if process is running via PID file.

        Args:
            pid_file: Path to PID file

        Returns:
            True if process is running
        """
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists (signal 0 doesn't actually send a signal)
            os.kill(pid, 0)
            return True
        except (ValueError, OSError, ProcessLookupError):
            return False

    def can_restart(self, process_name: str, max_restarts: int) -> bool:
        """
        Check if process can be restarted (within rate limit).

        Args:
            process_name: Name of the process
            max_restarts: Maximum restarts allowed per hour

        Returns:
            True if process can be restarted
        """
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
        """
        Start a process and track its PID.

        Args:
            process_name: Name of the process
            config: Process configuration dict
        """
        logger.info(f"Starting {process_name}...")

        # Start process in new session so it doesn't get killed when watchdog stops
        proc = subprocess.Popen(
            config['command'].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Write PID file
        pid_file = Path(config['pid_file'])
        pid_file.write_text(str(proc.pid))

        # Track restart
        self.restart_history.setdefault(process_name, []).append(time.time())

        logger.info(f"{process_name} started with PID {proc.pid}")

    def check_and_restart(self):
        """Check all processes and restart if needed"""
        for name, config in PROCESSES.items():
            pid_file = Path(config['pid_file'])

            if not self.is_process_running(pid_file):
                logger.warning(f"{name} not running, attempting restart...")

                if self.can_restart(name, config['max_restarts_per_hour']):
                    self.start_process(name, config)

                    if self.notifier:
                        self.notifier.alert(
                            level='WARNING',
                            component=name,
                            message=f"{name} was restarted by watchdog"
                        )
                else:
                    logger.critical(f"{name} exceeded max restarts, manual intervention required")

                    if self.notifier:
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
