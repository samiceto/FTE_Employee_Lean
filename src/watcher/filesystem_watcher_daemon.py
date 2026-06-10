from pathlib import Path
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
import time, shutil, logging
import sys
import os
import signal
import traceback
import threading
from datetime import datetime

VAULT = Path("/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault")
INBOX = VAULT / "Inbox"
NEEDS = VAULT / "Need_Action"

# --- Self-healing directory checks ---
def ensure_directories():
    """Ensure required directories exist with self-healing capability"""
    while not VAULT.exists():
        logging.error(f"Vault missing: {VAULT}")
        time.sleep(5)

    while not INBOX.exists():
        logging.error(f"Inbox missing: {INBOX}")
        time.sleep(5)

    while not NEEDS.exists():
        logging.error(f"Needs_Action missing: {NEEDS}")
        time.sleep(5)

ensure_directories()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler('/mnt/d/FTE_Employee/hackathon_zero/logs/watcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)

        # Ignore temp files (important on Windows)
        if src.name.startswith("~") or src.suffix == ".tmp":
            return

        try:
            # Verify source file exists before attempting move
            if not src.exists():
                logging.warning(f"Source file no longer exists: {src}")
                return

            dest = NEEDS / src.name

            # Add basic collision handling
            counter = 1
            original_dest = dest
            while dest.exists():
                stem = original_dest.stem
                suffix = original_dest.suffix
                dest = NEEDS / f"{stem}_{counter}{suffix}"
                counter += 1

            shutil.move(src, dest)

            # Log structured event
            logging.info(f"MOVED_FILE src={src.name} dest={dest.name} timestamp={datetime.now().isoformat()}")

        except PermissionError:
            logging.error(f"Permission denied moving file {src.name}")
        except FileNotFoundError:
            logging.error(f"Source file not found during move: {src.name}")
        except OSError as e:
            logging.error(f"OS error moving file {src.name}: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error moving file {src.name}: {str(e)}")
            logging.error(traceback.format_exc())

def signal_handler(signum, frame):
    logging.info("Received interrupt signal. Shutting down...")
    if 'observer' in globals():
        observer.stop()

def heartbeat_loop(logger):
    """Heartbeat function that logs every 30 seconds to confirm the watcher is alive"""
    while True:
        try:
            logger.info("💓 Heartbeat: File watcher is alive")
            time.sleep(30)  # Log heartbeat every 30 seconds
        except:
            break  # Exit if there's an issue with the heartbeat itself

def main():
    global observer
    observer = Observer()

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=heartbeat_loop, args=(logging.getLogger(),), daemon=True)
    heartbeat_thread.start()

    # Log structured startup event
    logging.info(f"STARTUP service=filesystem_watcher inbox_path={INBOX} needs_path={NEEDS} pid={os.getpid()}")

    try:
        observer.schedule(Handler(), str(INBOX), recursive=False)
        observer.start()
        logging.info(f"📡 Watching inbox at: {INBOX}")

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Main loop with enhanced error handling
        restart_count = 0
        while True:
            time.sleep(1)
            if not observer.is_alive():
                restart_count += 1
                logging.warning(f"Observer thread died, restart attempt #{restart_count}...")
                try:
                    observer.stop()
                    observer.join(timeout=5)  # Wait up to 5 seconds for clean shutdown
                except:
                    pass  # Continue even if stop/join fails

                # Create new observer instance
                observer = Observer()
                observer.schedule(Handler(), str(INBOX), recursive=False)
                observer.start()
                logging.info(f"Observer restarted successfully, attempt #{restart_count}")

    except KeyboardInterrupt:
        logging.info(f"INTERRUPT signal=SIGINT pid={os.getpid()}")
    except Exception as e:
        logging.error(f"CRASH reason=unexpected_error error='{str(e)}' traceback='{traceback.format_exc()}'")
    finally:
        try:
            observer.stop()
            observer.join(timeout=10)  # Wait up to 10 seconds for clean shutdown
        except:
            pass  # Ensure we don't hang during shutdown
        logging.info(f"SHUTDOWN service=filesystem_watcher pid={os.getpid()} exit_time={datetime.now().isoformat()}")

if __name__ == "__main__":
    main()