"""
Cloud Agent - Always-on agent that runs on Azure VM (24/7)

Responsibilities (DRAFT-ONLY - never executes final actions):
  • Email triage: reads Need_Action/email_replies/, drafts replies
  • Social drafts: creates draft posts for LinkedIn/Instagram/X
  • Odoo drafts: creates draft invoice/expense entries
  • Claim-by-move: moves tasks to In_Progress/cloud/ before processing
  • Status reporting: writes updates to Updates/cloud/

Security: Never stores or uses payment creds, banking tokens, or local secrets.
All output is draft markdown - Local Agent approves and executes.
"""
import os
import sys
import json
import shutil
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()
logger = logging.getLogger(__name__)

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq package not installed - AI drafting disabled")


AGENT_ID = "cloud_agent"
DRAFT_VERSION = "1.0"


class CloudAgent:
    """
    Always-on cloud agent. Triages email, drafts replies and social content,
    prepares Odoo entries. All output goes to Pending_Approval/cloud/ for
    Local Agent review before any action is taken.
    """

    def __init__(self, vault_path: str, model: str = "llama-3.3-70b-versatile"):
        self.vault = Path(vault_path)
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY")

        # Input folders (Cloud reads)
        self.needs_action = self.vault / "Need_Action"
        self.email_inbox = self.needs_action / "email_replies"
        self.social_inbox = self.needs_action / "social_posts"

        # Claim folder (Cloud owns while processing)
        self.in_progress = self.vault / "In_Progress" / "cloud"

        # Output folders (Cloud writes drafts)
        self.pending = self.vault / "Pending_Approval" / "cloud"
        self.email_drafts = self.pending / "email_drafts"
        self.social_drafts = self.pending / "social_drafts"
        self.odoo_drafts = self.pending / "odoo_drafts"

        # Status reporting
        self.updates = self.vault / "Updates" / "cloud"

        self._ensure_dirs()
        self.client = Groq(api_key=self.api_key) if GROQ_AVAILABLE and self.api_key else None
        self.stats = {"processed": 0, "drafts_created": 0, "errors": 0}

    def _ensure_dirs(self):
        for d in [self.in_progress, self.email_drafts, self.social_drafts,
                  self.odoo_drafts, self.updates]:
            d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Claim-by-move                                                       #
    # ------------------------------------------------------------------ #

    def _claim_task(self, task_file: Path) -> Optional[Path]:
        """Move task to In_Progress/cloud/ atomically. Returns new path or None if already claimed."""
        dest = self.in_progress / task_file.name
        if dest.exists():
            return None  # Already claimed by us (from a previous run that didn't finish)
        try:
            shutil.move(str(task_file), str(dest))
            logger.info(f"Claimed: {task_file.name}")
            return dest
        except (OSError, shutil.Error):
            return None  # Another agent claimed it first

    def _release_task(self, claimed_file: Path, destination: Path):
        """Move claimed task to final destination after drafting."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(claimed_file), str(destination))

    # ------------------------------------------------------------------ #
    #  AI drafting via Groq                                                #
    # ------------------------------------------------------------------ #

    def _call_groq(self, system: str, user: str) -> str:
        if not self.client:
            return "[AI unavailable - GROQ_API_KEY not set]"
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=800,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"[Draft generation failed: {e}]"

    # ------------------------------------------------------------------ #
    #  Email triage                                                        #
    # ------------------------------------------------------------------ #

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse simple YAML frontmatter from markdown."""
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

    def triage_emails(self) -> int:
        """Claim email tasks, draft replies, write to Pending_Approval/cloud/email_drafts/."""
        count = 0
        email_files = list(self.email_inbox.glob("*.md"))
        if not email_files:
            logger.debug("No new emails to triage")
            return 0

        for ef in email_files:
            claimed = self._claim_task(ef)
            if not claimed:
                continue

            try:
                content = claimed.read_text(encoding="utf-8")
                meta = self._parse_frontmatter(content)
                sender = meta.get("from", "Unknown")
                subject = meta.get("subject", "No Subject")
                priority = meta.get("priority", "normal")
                snippet = content.split("## Email Content")[-1][:600].strip() if "## Email Content" in content else ""

                system_prompt = (
                    "You are a professional email assistant. Write concise, polished email reply drafts. "
                    "Maintain a professional but friendly tone. Keep replies under 150 words."
                )
                user_prompt = (
                    f"Email received:\nFrom: {sender}\nSubject: {subject}\nPriority: {priority}\n\n"
                    f"Content preview:\n{snippet}\n\n"
                    "Write a professional reply draft. Include: greeting, response body, closing."
                )
                draft_body = self._call_groq(system_prompt, user_prompt)

                # Classify urgency
                urgency = "high" if priority == "high" else "normal"

                draft_id = f"EMAIL_DRAFT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{claimed.stem}"
                draft_content = f"""---
draft_id: {draft_id}
type: email_draft
source_task: {claimed.name}
created_by: {AGENT_ID}
created_at: {datetime.now(timezone.utc).isoformat()}
status: pending_approval
to: {sender}
subject: Re: {subject}
urgency: {urgency}
---

## Draft Reply

{draft_body}

---
## Approval Actions
- **Approve**: Move this file to `Approved/email_ready/`
- **Reject**: Move this file to `Rejected/` with reason
- **Edit**: Modify the draft above before approving

## Source Details
- Original task: `{claimed.name}`
- Original subject: `{subject}`
- From: `{sender}`
- Triaged by: Cloud Agent at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
                draft_file = self.email_drafts / f"{draft_id}.md"
                draft_file.write_text(draft_content, encoding="utf-8")

                # Move claimed task to In_Progress (keep there until local approves/rejects)
                logger.info(f"Email draft created: {draft_id}")
                self.stats["drafts_created"] += 1
                count += 1
                self.stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error triaging {ef.name}: {e}")
                self.stats["errors"] += 1
                # Return claimed task to inbox on error
                self._release_task(claimed, self.email_inbox / claimed.name)

        return count

    # ------------------------------------------------------------------ #
    #  Social post drafts                                                  #
    # ------------------------------------------------------------------ #

    def draft_social_posts(self) -> int:
        """Claim social post tasks, generate optimized drafts."""
        count = 0
        social_files = list(self.social_inbox.glob("*.md")) if self.social_inbox.exists() else []

        for sf in social_files:
            claimed = self._claim_task(sf)
            if not claimed:
                continue
            try:
                content = claimed.read_text(encoding="utf-8")
                meta = self._parse_frontmatter(content)
                platform = meta.get("platform", "linkedin")
                topic = meta.get("topic", "general")

                system_prompt = (
                    f"You are a social media expert for {platform}. "
                    "Write engaging, professional posts. Use relevant hashtags. "
                    f"LinkedIn: 150-300 words, professional. "
                    f"Instagram/X: punchy, 50-100 words with hashtags."
                )
                user_prompt = (
                    f"Create a {platform} post about: {topic}\n\n"
                    f"Raw content:\n{content[:400]}\n\n"
                    "Generate an optimized post draft."
                )
                draft_body = self._call_groq(system_prompt, user_prompt)

                draft_id = f"SOCIAL_DRAFT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{platform.upper()}"
                draft_content = f"""---
draft_id: {draft_id}
type: social_draft
platform: {platform}
source_task: {claimed.name}
created_by: {AGENT_ID}
created_at: {datetime.now(timezone.utc).isoformat()}
status: pending_approval
---

## Draft Post ({platform.title()})

{draft_body}

---
## Approval Actions
- **Approve**: Move to `Approved/social_ready/`
- **Reject**: Move to `Rejected/` with reason
- **Edit**: Modify draft above before approving

## Source Details
- Original task: `{claimed.name}`
- Platform: {platform}
- Drafted by: Cloud Agent at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
                draft_file = self.social_drafts / f"{draft_id}.md"
                draft_file.write_text(draft_content, encoding="utf-8")
                logger.info(f"Social draft created: {draft_id}")
                self.stats["drafts_created"] += 1
                count += 1
                self.stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error drafting social post {sf.name}: {e}")
                self.stats["errors"] += 1
                self._release_task(claimed, self.social_inbox / claimed.name)

        return count

    # ------------------------------------------------------------------ #
    #  Odoo draft entries                                                  #
    # ------------------------------------------------------------------ #

    def draft_odoo_entries(self) -> int:
        """
        Check In_Progress/cloud for tasks that mention invoices/expenses
        and create Odoo draft entries for local approval before posting.
        """
        count = 0
        # Look for invoice/expense tasks already in In_Progress
        in_progress_files = list(self.in_progress.glob("*.md"))

        for f in in_progress_files:
            content = f.read_text(encoding="utf-8").lower()
            if "invoice" not in content and "expense" not in content:
                continue
            # Skip if we already created an Odoo draft for this
            existing = list(self.odoo_drafts.glob(f"*{f.stem}*.md"))
            if existing:
                continue

            meta = self._parse_frontmatter(f.read_text(encoding="utf-8"))
            task_type = "invoice" if "invoice" in content else "expense"

            system_prompt = (
                "You are an accounting assistant. Extract structured accounting data from emails/tasks. "
                "Return a JSON object with: partner_name, description, amount, currency, type (invoice/expense), notes."
            )
            user_prompt = f"Extract accounting data from this task:\n\n{f.read_text(encoding='utf-8')[:600]}"
            raw = self._call_groq(system_prompt, user_prompt)

            draft_id = f"ODOO_DRAFT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{task_type.upper()}"
            draft_content = f"""---
draft_id: {draft_id}
type: odoo_draft
odoo_action: create_{task_type}
source_task: {f.name}
created_by: {AGENT_ID}
created_at: {datetime.now(timezone.utc).isoformat()}
status: pending_approval
---

## Odoo Draft Entry ({task_type.title()})

### Extracted Data
{raw}

### Odoo Action
- Action: `create_{task_type}` (DRAFT - not posted until Local approves)
- Approval required before posting to Odoo

---
## Approval Actions
- **Approve**: Move to `Approved/odoo_ready/` → Local will post to Odoo
- **Reject**: Move to `Rejected/` with reason

## Source Details
- Original task: `{f.name}`
- Drafted by: Cloud Agent at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
            draft_file = self.odoo_drafts / f"{draft_id}.md"
            draft_file.write_text(draft_content, encoding="utf-8")
            logger.info(f"Odoo draft created: {draft_id}")
            self.stats["drafts_created"] += 1
            count += 1

        return count

    # ------------------------------------------------------------------ #
    #  Status reporting                                                    #
    # ------------------------------------------------------------------ #

    def write_status_update(self):
        """Write current status to Updates/cloud/ for Local Agent to merge into Dashboard."""
        pending_emails = len(list(self.email_drafts.glob("*.md")))
        pending_social = len(list(self.social_drafts.glob("*.md")))
        pending_odoo = len(list(self.odoo_drafts.glob("*.md")))
        in_progress = len(list(self.in_progress.glob("*.md")))

        status_file = self.updates / f"status_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
        content = f"""---
agent: {AGENT_ID}
timestamp: {datetime.now(timezone.utc).isoformat()}
type: status_update
---

## Cloud Agent Status — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

| Metric | Value |
|--------|-------|
| Tasks processed this run | {self.stats['processed']} |
| Drafts created | {self.stats['drafts_created']} |
| Errors | {self.stats['errors']} |
| Currently in-progress | {in_progress} |
| Pending email drafts | {pending_emails} |
| Pending social drafts | {pending_social} |
| Pending Odoo drafts | {pending_odoo} |

### Health: {'✅ OK' if self.stats['errors'] == 0 else '⚠️ Errors detected'}
"""
        status_file.write_text(content, encoding="utf-8")
        logger.info(f"Status update written: {status_file.name}")

    # ------------------------------------------------------------------ #
    #  Main run                                                            #
    # ------------------------------------------------------------------ #

    def run_once(self) -> dict:
        """Single pass: triage emails, draft social posts, draft Odoo entries."""
        logger.info("Cloud Agent run starting...")
        self.stats = {"processed": 0, "drafts_created": 0, "errors": 0}

        emails = self.triage_emails()
        social = self.draft_social_posts()
        odoo = self.draft_odoo_entries()

        self.write_status_update()

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "emails_triaged": emails,
            "social_drafted": social,
            "odoo_drafted": odoo,
            "total_drafts": self.stats["drafts_created"],
            "errors": self.stats["errors"],
        }
        logger.info(f"Cloud Agent run complete: {summary}")
        return summary
