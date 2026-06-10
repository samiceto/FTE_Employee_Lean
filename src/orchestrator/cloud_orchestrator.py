"""
Cloud Orchestrator - Always-on loop for Azure VM

Runs Cloud Agent on a schedule (default every 5 minutes).
Reports health to Updates/cloud/ for Local Agent to consume.
Designed for 24/7 operation on Azure B1s VM.
"""
import os
import sys
import time
import json
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from agents.cloud_agent import CloudAgent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cloud_orchestrator] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/cloud_orchestrator.log"),
    ],
)
logger = logging.getLogger(__name__)

PID_FILE = "/tmp/cloud_orchestrator.pid"


class CloudOrchestrator:
    """
    Runs CloudAgent in a tight loop.
    - Writes PID file for watchdog
    - Handles SIGTERM/SIGINT gracefully
    - Exponential backoff on repeated errors
    """

    def __init__(self, vault_path: str, interval: int = 300, model: str = "llama-3.3-70b-versatile"):
        self.vault_path = vault_path
        self.interval = interval
        self.model = model
        self.running = False
        self.consecutive_errors = 0

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, *_):
        logger.info("Cloud Orchestrator shutting down gracefully...")
        self.running = False

    def _write_pid(self):
        Path(PID_FILE).write_text(str(os.getpid()))

    def _remove_pid(self):
        try:
            Path(PID_FILE).unlink(missing_ok=True)
        except Exception:
            pass

    def _write_heartbeat(self, vault: Path):
        """Write heartbeat so Local Agent knows Cloud is alive."""
        hb_file = vault / "Updates" / "cloud" / "heartbeat.md"
        hb_file.write_text(
            f"---\nagent: cloud_orchestrator\ntimestamp: {datetime.now(timezone.utc).isoformat()}\nstatus: running\n---\n\n"
            f"Cloud Orchestrator alive at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
            encoding="utf-8",
        )

    def run(self):
        self._write_pid()
        self.running = True
        vault = Path(self.vault_path)
        logger.info(f"Cloud Orchestrator started | vault={self.vault_path} | interval={self.interval}s")

        while self.running:
            try:
                agent = CloudAgent(vault_path=self.vault_path, model=self.model)
                result = agent.run_once()
                self._write_heartbeat(vault)
                self.consecutive_errors = 0

                logger.info(
                    f"Run complete — drafts={result['total_drafts']} "
                    f"errors={result['errors']} emails={result['emails_triaged']}"
                )
            except Exception as e:
                self.consecutive_errors += 1
                backoff = min(60 * self.consecutive_errors, 300)
                logger.error(f"Run failed (#{self.consecutive_errors}): {e} — backing off {backoff}s")
                time.sleep(backoff)
                continue

            logger.debug(f"Sleeping {self.interval}s until next run...")
            # Sleep in small chunks so SIGTERM is responsive
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

        self._remove_pid()
        logger.info("Cloud Orchestrator stopped.")


def main():
    parser = argparse.ArgumentParser(description="Cloud Orchestrator — always-on Azure agent")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./ai_employee_vault"))
    parser.add_argument("--interval", type=int, default=300, help="Seconds between runs (default 300)")
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        agent = CloudAgent(vault_path=args.vault, model=args.model)
        result = agent.run_once()
        print(json.dumps(result, indent=2))
        return

    orch = CloudOrchestrator(vault_path=args.vault, interval=args.interval, model=args.model)
    orch.run()


if __name__ == "__main__":
    main()
