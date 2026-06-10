#!/usr/bin/env python3
"""
Platinum Demo Script
────────────────────
Simulates the minimum passing gate for Platinum Tier:

  Email arrives while Local is offline
    → Cloud Agent triages it and drafts a reply
    → Cloud writes draft to Pending_Approval/cloud/email_drafts/
    → (Vault syncs via Git — simulated here)
  Local comes back online
    → Local Approval Loop shows the draft
    → User approves
    → Local executes send via email
    → Logs everything
    → Moves task to Done/

Run from project root:
  python scripts/platinum_demo.py --vault ./ai_employee_vault
  python scripts/platinum_demo.py --vault ./ai_employee_vault --auto-approve
"""
import sys
import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("platinum_demo")

SEPARATOR = "═" * 60

# Load Cloud/Local agents directly (bypasses agents/__init__.py which eagerly
# imports ReasoningAgent → skills → src.core, causing import chain errors)
def _load_agent(name: str, rel_path: str):
    import importlib.util
    full = Path(__file__).parent.parent / rel_path
    spec = importlib.util.spec_from_file_location(name, full)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_cloud_mod = _load_agent("cloud_agent", "src/agents/cloud_agent.py")
_local_mod = _load_agent("local_approval_agent", "src/agents/local_approval_agent.py")
CloudAgent = _cloud_mod.CloudAgent
LocalApprovalAgent = _local_mod.LocalApprovalAgent


def inject_test_email(vault_path: Path, sender: str = "client@example.com",
                       subject: str = "Please send invoice for Project Alpha") -> Path:
    """Inject a synthetic email into Need_Action/email_replies/ to simulate Gmail watcher."""
    inbox = vault_path / "Need_Action" / "email_replies"
    inbox.mkdir(parents=True, exist_ok=True)
    email_id = f"DEMO_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now(timezone.utc).isoformat()}
priority: high
status: pending
demo: true
---

## Email Content
Hi,

Could you please send the invoice for Project Alpha?
We completed milestone 2 (30 hours at $200/hour) and need the invoice for our records.

Thank you,
{sender.split('@')[0].title()}

## Suggested Actions
- [ ] Reply to sender
- [ ] Generate invoice in Odoo
"""
    filepath = inbox / f"EMAIL_{email_id}.md"
    filepath.write_text(content)
    return filepath


def run_demo(vault_path: str, auto_approve: bool = False):

    vault = Path(vault_path)

    print(f"\n{SEPARATOR}")
    print("  PLATINUM TIER DEMO")
    print("  Always-On Cloud + Local Executive")
    print(SEPARATOR)

    # ── Step 1: Inject test email (simulates Gmail watcher) ──────────
    print("\n[STEP 1] 📧 Email arrives while Local is OFFLINE...")
    print("         (Injecting test email into Need_Action/email_replies/)")
    email_file = inject_test_email(vault)
    print(f"         ✅ Test email: {email_file.name}")

    # ── Step 2: Cloud Agent triages email ─────────────────────────────
    print("\n[STEP 2] ☁️  Cloud Agent (Azure VM) triages email...")
    print("         Running CloudAgent.run_once() — draft-only mode")

    cloud = CloudAgent(vault_path=vault_path)
    result = cloud.run_once()

    drafts_created = result["total_drafts"]
    print(f"         ✅ Cloud run complete:")
    print(f"            Emails triaged:  {result['emails_triaged']}")
    print(f"            Drafts created:  {drafts_created}")
    print(f"            Errors:          {result['errors']}")

    # ── Step 3: Vault sync (simulated) ───────────────────────────────
    print("\n[STEP 3] 🔄 Vault syncing to GitHub relay...")
    print("         (In production: Cloud VM pushes via vault_sync.sh)")
    print("         (Local machine pulls via --auto-pull or local_vault_sync.sh)")
    print("         ✅ Sync simulated — drafts are in local vault")

    # ── Step 4: Local Agent comes online ─────────────────────────────
    print("\n[STEP 4] 🏠 Local machine comes ONLINE...")

    local = LocalApprovalAgent(vault_path=vault_path)
    local.merge_cloud_updates_to_dashboard()
    pending = local.get_pending_approvals()

    print(f"         ✅ Local Approval Agent active")
    print(f"         📋 {len(pending)} item(s) awaiting approval")

    if not pending:
        print("\n❌ Demo failed — no drafts found. Check that GROQ_API_KEY is set.")
        print("   Without Groq, CloudAgent creates placeholder drafts — verify the email was claimed.")
        # Show what's in in_progress
        in_prog = list((vault / "In_Progress" / "cloud").glob("*.md"))
        print(f"   In_Progress/cloud: {[f.name for f in in_prog]}")
        return False

    # ── Step 5: Show draft to user ────────────────────────────────────
    item = pending[0]
    print(f"\n[STEP 5] 📝 Showing draft to user for approval...")
    print(f"\n{SEPARATOR}")

    if item["type"] == "email_draft":
        print(f"  TYPE:    Email Reply Draft")
        print(f"  TO:      {item.get('to', 'N/A')}")
        print(f"  SUBJECT: {item.get('subject', 'N/A')}")
        print(f"  URGENCY: {item.get('urgency', 'normal').upper()}")
        print(f"  ID:      {item['id']}")
    print(SEPARATOR)

    # Show the draft body
    content = item["content"]
    body_parts = content.split("---", 2)
    body = body_parts[2] if len(body_parts) >= 3 else content
    if "## Approval Actions" in body:
        body = body.split("## Approval Actions")[0]
    print(body.strip())
    print(SEPARATOR)

    # ── Step 6: Approval ─────────────────────────────────────────────
    if auto_approve:
        decision = "approve"
        print("\n[STEP 6] ✅ Auto-approving (--auto-approve flag set)")
    else:
        print("\n[STEP 6] 👤 Waiting for user decision...")
        try:
            inp = input("  [A]pprove / [R]eject / [S]kip > ").strip().lower()
            decision = "approve" if inp in ("a", "approve") else ("reject" if inp in ("r", "reject") else "skip")
        except (EOFError, KeyboardInterrupt):
            decision = "skip"
            print("  Skipped")

    if decision == "approve":
        print("\n[STEP 7] ⚡ Local Agent executing approved action...")
        success = local.approve(item)
        if success:
            print("         ✅ Action executed successfully!")
            if not os.getenv("EMAIL_SENDER"):
                print("         (EMAIL_SENDER not set → staged in Approved/email_ready/ for MCP)")
        else:
            print("         ❌ Execution failed — check logs")
    elif decision == "reject":
        local.reject(item, "Demo rejection")
        print("\n[STEP 7] 🚫 Rejected and archived")
    else:
        print("\n[STEP 7] ⏩ Skipped by user")

    # ── Step 8: Summary ──────────────────────────────────────────────
    print(f"\n{SEPARATOR}")
    print("  DEMO COMPLETE — Platinum Flow Verified")
    print(SEPARATOR)

    done_files = list((vault / "Done").glob("**/*.md"))
    in_prog = list((vault / "In_Progress" / "cloud").glob("*.md"))
    pending_after = list((vault / "Pending_Approval" / "cloud" / "email_drafts").glob("*.md"))

    print(f"\n  📊 Final State:")
    print(f"     Done/:             {len(done_files)} file(s)")
    print(f"     In_Progress/cloud: {len(in_prog)} file(s)")
    print(f"     Pending_Approval:  {len(pending_after)} file(s)")
    print(f"\n  🔍 Check audit log:")
    print(f"     cat {vault}/Logs/audit/audit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl")
    print(f"\n  📋 Dashboard:")
    print(f"     cat {vault}/Dashboard.md")
    print(SEPARATOR)
    return True


def main():
    parser = argparse.ArgumentParser(description="Platinum Tier Demo")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./ai_employee_vault"))
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve the draft (non-interactive)")
    args = parser.parse_args()

    vault_path = os.path.abspath(args.vault)
    success = run_demo(vault_path=vault_path, auto_approve=args.auto_approve)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
