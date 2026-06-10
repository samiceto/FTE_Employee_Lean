"""
Local Approval Loop - Interactive CLI for reviewing and approving Cloud Agent drafts

Usage:
  python -m src.orchestrator.local_approval_loop --vault ./ai_employee_vault
  python -m src.orchestrator.local_approval_loop --vault ./ai_employee_vault --auto-pull
  python -m src.orchestrator.local_approval_loop --watch  # continuous mode

Platinum Demo flow:
  1. Pull latest vault from GitHub (git pull)
  2. Show pending approvals from Cloud Agent
  3. User reviews each draft
  4. On approve: execute action (send email, stage social post, etc.)
  5. On reject: archive with reason
  6. Push approved/done changes back to GitHub (git push)
"""
import os
import sys
import json
import time
import signal
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.local_approval_agent import LocalApprovalAgent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [local_approval] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

SEPARATOR = "─" * 60


def git_sync(vault_path: str, direction: str = "pull"):
    """Pull latest vault changes from GitHub relay."""
    try:
        cwd = vault_path
        if direction == "pull":
            result = subprocess.run(
                ["git", "pull", "--rebase", "origin", "main"],
                cwd=cwd, capture_output=True, text=True, timeout=30
            )
        else:
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd=cwd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                result = subprocess.run(
                    ["git", "commit", "-m", f"Local approval sync {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"],
                    cwd=cwd, capture_output=True, text=True, timeout=10
                )
            if result.returncode in (0, 1):  # 1 = nothing to commit
                result = subprocess.run(
                    ["git", "push", "origin", "main"],
                    cwd=cwd, capture_output=True, text=True, timeout=30
                )
        if result.returncode not in (0, 1):
            logger.warning(f"git {direction} warning: {result.stderr.strip()}")
        else:
            logger.info(f"git {direction} OK")
    except subprocess.TimeoutExpired:
        logger.warning(f"git {direction} timed out")
    except FileNotFoundError:
        logger.warning("git not found — vault sync skipped")
    except Exception as e:
        logger.warning(f"git {direction} failed: {e}")


def display_draft(item: dict, index: int, total: int):
    """Pretty-print a draft for user review."""
    print(f"\n{SEPARATOR}")
    print(f"  DRAFT {index}/{total}  |  {item['type'].upper().replace('_', ' ')}")
    print(SEPARATOR)

    if item["type"] == "email_draft":
        print(f"  To:      {item.get('to', 'N/A')}")
        print(f"  Subject: {item.get('subject', 'N/A')}")
        print(f"  Urgency: {item.get('urgency', 'normal').upper()}")
    elif item["type"] == "social_draft":
        print(f"  Platform: {item.get('platform', 'N/A').upper()}")
    elif item["type"] == "odoo_draft":
        print(f"  Action: {item.get('odoo_action', 'N/A')}")

    print(f"  Draft ID: {item['id']}")
    created = item.get("created_at", "")[:19].replace("T", " ") if item.get("created_at") else "unknown"
    print(f"  Created:  {created} UTC")
    print(SEPARATOR)

    # Show the draft body
    content = item["content"]
    parts = content.split("---", 2)
    if len(parts) >= 3:
        body = parts[2]
    else:
        body = content

    # Show up to first approval section
    if "## Approval Actions" in body:
        body = body.split("## Approval Actions")[0]
    print(body.strip())
    print(SEPARATOR)


def prompt_decision() -> str:
    """Ask user for approval decision. Returns 'approve', 'reject', 'skip', 'quit'."""
    while True:
        try:
            choice = input("\n  [A]pprove  [R]eject  [S]kip  [Q]uit  [E]dit > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"
        if choice in ("a", "approve"):
            return "approve"
        if choice in ("r", "reject"):
            return "reject"
        if choice in ("s", "skip"):
            return "skip"
        if choice in ("q", "quit"):
            return "quit"
        if choice in ("e", "edit"):
            return "edit"
        print("  Invalid choice — try again")


def run_interactive(agent: LocalApprovalAgent, auto_sync: bool, vault_path: str):
    """Interactive approval session."""
    if auto_sync:
        print("\n[Syncing vault from GitHub...]")
        git_sync(vault_path, "pull")

    result = agent.run_once()
    pending = result["pending"]

    if not pending:
        print("\n✅ No pending approvals from Cloud Agent.")
        return 0

    approved = rejected = skipped = 0
    total = len(pending)
    print(f"\n📋 {total} item(s) awaiting your approval\n")

    for i, item in enumerate(pending, 1):
        display_draft(item, i, total)
        decision = prompt_decision()

        if decision == "quit":
            print("\n👋 Exiting approval session.")
            break
        elif decision == "approve":
            print(f"\n  ⏳ Executing {item['type']}...")
            success = agent.approve(item)
            if success:
                print(f"  ✅ Done — {item['id']}")
                approved += 1
            else:
                print(f"  ❌ Execution failed — check logs")
        elif decision == "reject":
            try:
                reason = input("  Rejection reason (Enter to skip): ").strip() or "User rejected"
            except (EOFError, KeyboardInterrupt):
                reason = "User rejected"
            agent.reject(item, reason)
            print(f"  🚫 Rejected — moved to Rejected/")
            rejected += 1
        elif decision == "edit":
            print(f"\n  ✏️  Opening draft file for editing...")
            print(f"  File: {item['file']}")
            editor = os.getenv("EDITOR", "nano")
            try:
                subprocess.run([editor, str(item["file"])])
                print("  After editing, re-run to approve the edited draft.")
            except Exception as e:
                print(f"  Could not open editor: {e}")
            skipped += 1
        else:  # skip
            print(f"  ⏩ Skipped")
            skipped += 1

    print(f"\n{SEPARATOR}")
    print(f"  Session summary: ✅ {approved} approved | 🚫 {rejected} rejected | ⏩ {skipped} skipped")
    print(SEPARATOR)

    if auto_sync and (approved + rejected) > 0:
        print("\n[Pushing approved actions to GitHub...]")
        git_sync(vault_path, "push")

    return approved


def run_watch_mode(vault_path: str, interval: int = 60, auto_sync: bool = True):
    """Watch for new approvals continuously, notify user."""
    running = True

    def _stop(*_):
        nonlocal running
        running = False
        print("\nStopping watch mode...")

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    print(f"👀 Watch mode: checking every {interval}s for new approvals (Ctrl+C to stop)")

    while running:
        agent = LocalApprovalAgent(vault_path=vault_path)
        if auto_sync:
            git_sync(vault_path, "pull")
        result = agent.run_once()
        count = result["pending_count"]

        if count > 0:
            print(f"\n🔔 {count} item(s) need approval!")
            run_interactive(agent, auto_sync=False, vault_path=vault_path)

        for _ in range(interval):
            if not running:
                break
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Local Approval Loop — review Cloud Agent drafts")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./ai_employee_vault"))
    parser.add_argument("--auto-pull", action="store_true", help="Git pull before showing approvals")
    parser.add_argument("--watch", action="store_true", help="Watch mode: poll continuously")
    parser.add_argument("--interval", type=int, default=60, help="Watch mode poll interval (seconds)")
    parser.add_argument("--list", action="store_true", help="Just list pending approvals and exit")
    args = parser.parse_args()

    vault_path = os.path.abspath(args.vault)

    if args.list:
        agent = LocalApprovalAgent(vault_path=vault_path)
        result = agent.run_once()
        print(json.dumps(
            [{"id": p["id"], "type": p["type"], "urgency": p.get("urgency", "normal")} for p in result["pending"]],
            indent=2
        ))
        return

    if args.watch:
        run_watch_mode(vault_path=vault_path, interval=args.interval, auto_sync=args.auto_pull)
        return

    agent = LocalApprovalAgent(vault_path=vault_path)
    run_interactive(agent, auto_sync=args.auto_pull, vault_path=vault_path)


if __name__ == "__main__":
    main()
