"""
Local Approval Agent - Executive agent that runs on the local machine

Responsibilities:
  • Watches Pending_Approval/cloud/ for drafts from Cloud Agent
  • Presents drafts to user for approval
  • On approval: executes action (send email, post social, post to Odoo)
  • Merges Updates/cloud/ status updates into Dashboard.md (single-writer)
  • Moves completed tasks to Done/
  • Maintains full audit trail

Security:
  • Has access to all credentials (.env)
  • WhatsApp sessions, payment tokens, banking creds stay local
  • Cloud never touches these
"""
import os
import sys
import json
import shutil
import smtplib
import logging
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()
logger = logging.getLogger(__name__)

AGENT_ID = "local_approval_agent"
DASHBOARD_FILE = "Dashboard.md"


class LocalApprovalAgent:
    """
    Reviews cloud drafts and executes approved actions.
    Is the single writer for Dashboard.md.
    """

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)

        # Input: Cloud drafts waiting for approval
        self.pending_cloud = self.vault / "Pending_Approval" / "cloud"
        self.email_drafts = self.pending_cloud / "email_drafts"
        self.social_drafts = self.pending_cloud / "social_drafts"
        self.odoo_drafts = self.pending_cloud / "odoo_drafts"

        # Input: Cloud status updates
        self.cloud_updates = self.vault / "Updates" / "cloud"

        # Execution input folders (Local writes here after approval)
        self.email_ready = self.vault / "Approved" / "email_ready"
        self.social_ready = self.vault / "Approved" / "social_ready"
        self.odoo_ready = self.vault / "Approved" / "odoo_ready"

        # Archive
        self.done = self.vault / "Done"
        self.rejected = self.vault / "Rejected"

        # Email config from env
        self.email_sender = os.getenv("EMAIL_SENDER", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")

        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.email_ready, self.social_ready, self.odoo_ready,
                  self.done / "email", self.done / "social", self.done / "odoo",
                  self.rejected]:
            d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Parse frontmatter                                                   #
    # ------------------------------------------------------------------ #

    def _parse_frontmatter(self, content: str) -> dict:
        meta = {}
        if not content.startswith("---"):
            return meta
        parts = content.split("---", 2)
        if len(parts) < 3:
            return meta
        for line in parts[1].strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        return meta

    def _get_draft_body(self, content: str) -> str:
        """Extract the actual draft text (after frontmatter, before approval actions)."""
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            body = content
        # Stop at approval section
        if "## Approval Actions" in body:
            body = body.split("## Approval Actions")[0]
        return body.strip()

    # ------------------------------------------------------------------ #
    #  Pending draft discovery                                             #
    # ------------------------------------------------------------------ #

    def get_pending_approvals(self) -> list[dict]:
        """Return all pending drafts sorted by urgency."""
        items = []
        for draft_file in sorted(self.email_drafts.glob("*.md")):
            content = draft_file.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            items.append({
                "file": draft_file,
                "type": "email_draft",
                "id": meta.get("draft_id", draft_file.stem),
                "to": meta.get("to", "unknown"),
                "subject": meta.get("subject", "No Subject"),
                "urgency": meta.get("urgency", "normal"),
                "created_at": meta.get("created_at", ""),
                "content": content,
                "meta": meta,
            })
        for draft_file in sorted(self.social_drafts.glob("*.md")):
            content = draft_file.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            items.append({
                "file": draft_file,
                "type": "social_draft",
                "id": meta.get("draft_id", draft_file.stem),
                "platform": meta.get("platform", "unknown"),
                "urgency": "normal",
                "created_at": meta.get("created_at", ""),
                "content": content,
                "meta": meta,
            })
        for draft_file in sorted(self.odoo_drafts.glob("*.md")):
            content = draft_file.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            items.append({
                "file": draft_file,
                "type": "odoo_draft",
                "id": meta.get("draft_id", draft_file.stem),
                "odoo_action": meta.get("odoo_action", "unknown"),
                "urgency": "normal",
                "created_at": meta.get("created_at", ""),
                "content": content,
                "meta": meta,
            })
        # High urgency first
        items.sort(key=lambda x: (0 if x["urgency"] == "high" else 1, x["created_at"]))
        return items

    # ------------------------------------------------------------------ #
    #  Approval & rejection                                                #
    # ------------------------------------------------------------------ #

    def approve(self, item: dict) -> bool:
        """Approve a draft: execute action and archive."""
        try:
            draft_type = item["type"]
            if draft_type == "email_draft":
                return self._execute_email(item)
            elif draft_type == "social_draft":
                return self._execute_social(item)
            elif draft_type == "odoo_draft":
                return self._execute_odoo(item)
            else:
                logger.error(f"Unknown draft type: {draft_type}")
                return False
        except Exception as e:
            logger.error(f"Approval execution failed for {item['id']}: {e}")
            return False

    def reject(self, item: dict, reason: str = "User rejected"):
        """Reject a draft: move to Rejected/ with reason."""
        src = item["file"]
        rejection_note = f"\n\n---\n## Rejected\n- **Reason:** {reason}\n- **Rejected at:** {datetime.now(timezone.utc).isoformat()}\n- **By:** {AGENT_ID}\n"
        content = src.read_text(encoding="utf-8") + rejection_note
        dest = self.rejected / src.name
        dest.write_text(content, encoding="utf-8")
        src.unlink()

        # Also release the In_Progress claim so Cloud can re-process if needed
        source_task = item["meta"].get("source_task", "")
        if source_task:
            in_progress_file = self.vault / "In_Progress" / "cloud" / source_task
            if in_progress_file.exists():
                shutil.move(str(in_progress_file), str(self.vault / "Need_Action" / "email_replies" / source_task))

        logger.info(f"Rejected: {item['id']} — {reason}")
        self._log_action("rejected", item, {"reason": reason})

    # ------------------------------------------------------------------ #
    #  Email execution                                                     #
    # ------------------------------------------------------------------ #

    def _execute_email(self, item: dict) -> bool:
        """Send approved email draft via SMTP."""
        to_addr = item["to"]
        subject = item["subject"]
        body = self._get_draft_body(item["content"])

        # Strip markdown headers to get clean body text
        lines = [l for l in body.splitlines() if not l.startswith("#")]
        clean_body = "\n".join(lines).strip()

        if not self.email_sender or not self.email_password:
            logger.warning("EMAIL_SENDER/EMAIL_PASSWORD not set — writing to email_ready/ for manual send")
            self._stage_for_manual_send(item, clean_body)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_sender
            msg["To"] = to_addr
            msg.attach(MIMEText(clean_body, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, to_addr, msg.as_string())

            logger.info(f"Email sent to {to_addr}: {subject}")
            self._archive_item(item, "email")
            self._log_action("email_sent", item, {"to": to_addr, "subject": subject})
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def _stage_for_manual_send(self, item: dict, body: str):
        """Write email to email_ready/ for manual send via MCP Email server."""
        ready_file = self.email_ready / item["file"].name
        content = item["content"]
        # Stamp as ready for MCP execution
        content += f"\n\n---\n## Ready for MCP Send\n- **Status:** approved, queued for email MCP\n- **Approved at:** {datetime.now(timezone.utc).isoformat()}\n"
        ready_file.write_text(content, encoding="utf-8")
        item["file"].unlink()
        logger.info(f"Email staged for MCP send: {ready_file.name}")

    # ------------------------------------------------------------------ #
    #  Social execution                                                    #
    # ------------------------------------------------------------------ #

    def _execute_social(self, item: dict) -> bool:
        """Stage approved social draft for social watcher execution."""
        platform = item["meta"].get("platform", "linkedin")
        # Route to the appropriate Approved/ folder that social watchers poll
        platform_map = {
            "linkedin": self.vault / "Approved" / "linkedin",
            "instagram": self.vault / "Approved" / "instagram",
            "x": self.vault / "Approved" / "x",
            "twitter": self.vault / "Approved" / "x",
            "facebook": self.vault / "Approved" / "facebook",
        }
        target_dir = platform_map.get(platform.lower(), self.social_ready)
        target_dir.mkdir(parents=True, exist_ok=True)

        body = self._get_draft_body(item["content"])
        # Write clean post file for watcher
        post_content = f"---\napproved_at: {datetime.now(timezone.utc).isoformat()}\napproved_by: {AGENT_ID}\nplatform: {platform}\n---\n\n{body}"
        dest = target_dir / item["file"].name
        dest.write_text(post_content, encoding="utf-8")
        item["file"].unlink()

        logger.info(f"Social post staged for {platform}: {dest.name}")
        self._archive_item(item, "social")
        self._log_action("social_staged", item, {"platform": platform})
        return True

    # ------------------------------------------------------------------ #
    #  Odoo execution                                                      #
    # ------------------------------------------------------------------ #

    def _execute_odoo(self, item: dict) -> bool:
        """Stage approved Odoo entry for Odoo MCP execution."""
        ready_file = self.odoo_ready / item["file"].name
        content = item["content"] + f"\n\n---\n## Ready for Odoo MCP\n- **Approved at:** {datetime.now(timezone.utc).isoformat()}\n- **Approved by:** {AGENT_ID}\n"
        ready_file.write_text(content, encoding="utf-8")
        item["file"].unlink()

        logger.info(f"Odoo entry staged: {ready_file.name}")
        self._archive_item(item, "odoo")
        self._log_action("odoo_staged", item, {"action": item["meta"].get("odoo_action", "unknown")})
        return True

    # ------------------------------------------------------------------ #
    #  Archive                                                             #
    # ------------------------------------------------------------------ #

    def _archive_item(self, item: dict, category: str):
        """Move source task file from In_Progress to Done."""
        source_task = item["meta"].get("source_task", "")
        if source_task:
            src = self.vault / "In_Progress" / "cloud" / source_task
            if src.exists():
                dest = self.done / source_task
                shutil.move(str(src), str(dest))

    # ------------------------------------------------------------------ #
    #  Dashboard merge (single-writer)                                     #
    # ------------------------------------------------------------------ #

    def merge_cloud_updates_to_dashboard(self):
        """
        Merge Updates/cloud/*.md status files into Dashboard.md.
        Local Agent is the ONLY writer to Dashboard.md.
        """
        update_files = sorted(self.cloud_updates.glob("status_*.md"))
        if not update_files:
            return

        dashboard_path = self.vault / DASHBOARD_FILE
        current = dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else "# Dashboard\n"

        # Collect latest status from cloud
        latest_status = []
        for uf in update_files:
            content = uf.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            ts = meta.get("timestamp", "")
            latest_status.append((ts, content))

        latest_status.sort(key=lambda x: x[0], reverse=True)
        if not latest_status:
            return

        # Update the Cloud Agent Status section in Dashboard
        cloud_section = f"""
## ☁️ Cloud Agent Status
*Last synced: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — by Local Agent*

{latest_status[0][1].split('---', 2)[-1].strip()}

"""
        marker = "## ☁️ Cloud Agent Status"
        if marker in current:
            before = current[:current.index(marker)]
            after_raw = current[current.index(marker):]
            # Find next top-level section
            next_section = after_raw.find("\n## ", 1)
            after = after_raw[next_section:] if next_section != -1 else ""
            new_dashboard = before + cloud_section + after
        else:
            new_dashboard = current.rstrip() + "\n\n" + cloud_section

        dashboard_path.write_text(new_dashboard, encoding="utf-8")

        # Archive processed updates
        archive_dir = self.cloud_updates / "processed"
        archive_dir.mkdir(exist_ok=True)
        for uf in update_files:
            shutil.move(str(uf), str(archive_dir / uf.name))

        logger.info(f"Merged {len(update_files)} cloud updates into Dashboard.md")

    # ------------------------------------------------------------------ #
    #  Audit logging                                                       #
    # ------------------------------------------------------------------ #

    def _log_action(self, action: str, item: dict, extra: dict = None):
        log_dir = self.vault / "Logs" / "audit"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"audit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": AGENT_ID,
            "action": action,
            "draft_id": item.get("id", ""),
            "draft_type": item.get("type", ""),
            **(extra or {}),
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    # ------------------------------------------------------------------ #
    #  Main run                                                            #
    # ------------------------------------------------------------------ #

    def run_once(self) -> dict:
        """Merge updates, return list of pending approvals for review."""
        self.merge_cloud_updates_to_dashboard()
        pending = self.get_pending_approvals()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pending_count": len(pending),
            "pending": pending,
        }
