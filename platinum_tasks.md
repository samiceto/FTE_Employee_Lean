# Platinum Tier Implementation Tasks

**Target:** Always-On Cloud + Local Executive (Production-ish AI Employee)
**Estimated Time:** 60+ hours
**Status:** Not Started
**Prerequisites:** Gold Tier Complete ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Summary](#architecture-summary)
3. [Phase 0: Pre-Implementation Planning](#phase-0-pre-implementation-planning)
4. [Phase 1: Cloud Infrastructure Setup](#phase-1-cloud-infrastructure-setup)
5. [Phase 2: Vault Sync & File-Based Delegation](#phase-2-vault-sync--file-based-delegation)
6. [Phase 3: Work-Zone Specialization](#phase-3-work-zone-specialization)
7. [Phase 4: Cloud Odoo Deployment](#phase-4-cloud-odoo-deployment)
8. [Phase 5: Security & Secrets Management](#phase-5-security--secrets-management)
9. [Phase 6: Health Monitoring & Always-On Operations](#phase-6-health-monitoring--always-on-operations)
10. [Phase 7: Integration Testing & Platinum Demo](#phase-7-integration-testing--platinum-demo)
11. [Phase 8 (Optional): Agent-to-Agent Upgrade](#phase-8-optional-agent-to-agent-upgrade)
12. [Testing Checklist](#testing-checklist)
13. [Success Criteria](#success-criteria)

---

## Overview

### What is Platinum Tier?

Platinum Tier transforms the AI Employee into a distributed system with:
- **Cloud Agent**: Always-on (24/7) handling email triage, social drafts
- **Local Agent**: Executive mode - handles approvals, WhatsApp, payments, final actions
- **Synced Vault**: Git-based coordination between agents
- **Work-Zone Ownership**: Clear domain boundaries preventing conflicts
- **Security First**: Secrets never leave local machine

### Key Principles

1. **Draft-Only Cloud**: Cloud never executes final actions (sends emails, posts content, makes payments)
2. **Approval-Based Local**: Local agent is the executive - makes all final decisions
3. **File-Based Communication**: Agents coordinate through structured vault folders (Phase 1)
4. **Claim-by-Move**: First agent to claim a task owns it (prevents double-work)
5. **Audit Everything**: All actions logged with agent attribution

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLOUD AGENT (24/7)                          │
│  Oracle Cloud Free VM / AWS / etc.                               │
│                                                                   │
│  Responsibilities:                                                │
│  • Email monitoring (Gmail watcher)                              │
│  • Email triage + draft replies                                  │
│  • Social post drafts (LinkedIn/Instagram/X)                     │
│  • Schedule social posts (draft-only)                            │
│  • Odoo accounting drafts (via MCP)                              │
│  • Write to: /Pending_Approval/cloud/                           │
│  • Write to: /Updates/cloud/                                     │
│                                                                   │
│  Does NOT have access to:                                        │
│  • WhatsApp sessions                                             │
│  • Payment credentials                                           │
│  • Banking tokens                                                │
│  • .env secrets                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Git Sync (Vault)
                            │ (markdown + state only)
                            │
┌─────────────────────────────────────────────────────────────────┐
│                      LOCAL AGENT (On-Demand)                     │
│  User's Local Machine                                            │
│                                                                   │
│  Responsibilities:                                                │
│  • Review /Pending_Approval/cloud/                               │
│  • Execute approved actions (send emails, post content)          │
│  • WhatsApp monitoring + responses                               │
│  • Payment execution                                             │
│  • Banking operations                                            │
│  • Final Odoo posting (invoices, payments)                       │
│  • Update Dashboard.md (single-writer)                          │
│  • Merge /Updates/cloud/ into Dashboard.md                       │
│                                                                   │
│  Has access to:                                                  │
│  • All credentials (.env)                                        │
│  • WhatsApp sessions                                             │
│  • Payment tokens                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SYNCED VAULT STRUCTURE                         │
│                                                                   │
│  ai_employee_vault/                                              │
│  ├── Need_Action/         ← Both agents read                     │
│  │   ├── email_replies/   ← Cloud claims by moving               │
│  │   ├── social_posts/    ← Cloud claims by moving               │
│  │   ├── business_tasks/  ← Local claims by moving               │
│  │   └── whatsapp/        ← Local only (not synced)              │
│  │                                                                │
│  ├── In_Progress/         ← Claim-by-move ownership              │
│  │   ├── cloud/           ← Cloud's claimed tasks                │
│  │   └── local/           ← Local's claimed tasks                │
│  │                                                                │
│  ├── Pending_Approval/    ← Cloud writes drafts                  │
│  │   └── cloud/                                                  │
│  │       ├── email_drafts/                                       │
│  │       ├── social_drafts/                                      │
│  │       └── odoo_drafts/                                        │
│  │                                                                │
│  ├── Approved/            ← Local approves for execution         │
│  │   ├── email_ready/     ← Local executes                       │
│  │   ├── social_ready/    ← Local executes                       │
│  │   └── odoo_ready/      ← Local executes                       │
│  │                                                                │
│  ├── Updates/             ← Cloud writes status                  │
│  │   └── cloud/                                                  │
│  │       └── status_*.md  ← Local merges into Dashboard         │
│  │                                                                │
│  ├── Dashboard.md         ← Local owns (single-writer)           │
│  ├── Plans/               ← Both agents write (separate files)   │
│  ├── Done/                ← Both agents archive                  │
│  └── Logs/                ← Both agents log (timestamped)        │
│                                                                   │
│  SYNC MECHANISM: Git (recommended) or Syncthing                  │
│                                                                   │
│  .gitignore ensures secrets never sync:                          │
│  • .env                                                          │
│  • .env.*                                                        │
│  • whatsapp_session/                                             │
│  • *_token.json                                                  │
│  • credentials.json                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Pre-Implementation Planning

**Estimated Time:** 2 hours
**Goal:** Understand requirements, design architecture, prepare tools

### Tasks

- [ ] **0.1 Review Platinum Requirements** (15 min)
  - Read platinum tier specifications
  - Identify all deliverables
  - Document acceptance criteria

- [ ] **0.2 Choose Cloud Provider** (30 min)
  - Option A: Oracle Cloud Free Tier (recommended for $0 cost)
    - VM.Standard.E2.1.Micro (1GB RAM, 1 OCPU)
    - 200GB block storage
    - Always Free tier
  - Option B: AWS Free Tier (12 months free)
    - t2.micro (1GB RAM)
    - 30GB storage
  - Option C: Google Cloud Free Tier
  - Decision: `_______________`

- [ ] **0.3 Choose Vault Sync Method** (15 min)
  - Option A: Git (recommended - full audit history)
    - Pros: Version control, conflict resolution, audit trail
    - Cons: Requires git knowledge
  - Option B: Syncthing (real-time sync)
    - Pros: Automatic, real-time
    - Cons: No audit trail, harder debugging
  - Decision: `_______________`

- [ ] **0.4 Design Work-Zone Boundaries** (30 min)
  - Document Cloud ownership:
    - Email triage (read-only)
    - Email draft replies
    - Social post drafts
    - Social post scheduling (draft calendar)
    - Odoo draft entries
  - Document Local ownership:
    - All approvals
    - WhatsApp (read + send)
    - Email sending (final execution)
    - Social posting (final execution)
    - Payments/banking
    - Odoo posting (final execution)

- [ ] **0.5 Design Vault Folder Structure** (30 min)
  - Create vault structure diagram
  - Define file naming conventions
  - Define claim-by-move rules
  - Define file format standards
  - Document single-writer rules

- [ ] **0.6 Create Implementation Checklist** (15 min)
  - Break down each phase into sub-tasks
  - Estimate time for each task
  - Identify dependencies
  - Create checkpoint system

**Checkpoint:** Architecture documented, decisions made, ready to start implementation

---

## Phase 1: Cloud Infrastructure Setup

**Estimated Time:** 8 hours
**Goal:** Deploy Cloud VM, install dependencies, configure network, set up AI Employee

### Tasks

#### 1.1 Cloud VM Provisioning (2 hours)

- [ ] **1.1.1 Create Oracle Cloud Account** (if using Oracle)
  - Sign up at cloud.oracle.com
  - Verify email
  - Configure home region

- [ ] **1.1.2 Provision VM Instance** (30 min)
  - Create VM.Standard.E2.1.Micro instance
  - Choose Ubuntu 22.04 LTS
  - Generate SSH key pair
  - Save private key securely
  - Note public IP: `_______________`

- [ ] **1.1.3 Configure Security List** (30 min)
  - Open ingress rules:
    - Port 22 (SSH)
    - Port 8069 (Odoo HTTPS)
    - Port 443 (Future web dashboard)
  - Restrict SSH to your IP (optional)

- [ ] **1.1.4 Configure Firewall on VM** (15 min)
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 8069/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

- [ ] **1.1.5 Test SSH Connection** (15 min)
  ```bash
  ssh -i ~/.ssh/oracle_key ubuntu@<VM_PUBLIC_IP>
  ```

#### 1.2 System Setup (2 hours)

- [ ] **1.2.1 Update System** (15 min)
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y build-essential git curl wget vim htop
  ```

- [ ] **1.2.2 Install Python 3.12** (30 min)
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt install -y python3.12 python3.12-venv python3.12-dev
  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
  ```

- [ ] **1.2.3 Install Playwright Dependencies** (30 min)
  ```bash
  sudo apt install -y libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2
  ```

- [ ] **1.2.4 Install PM2 for Process Management** (15 min)
  ```bash
  curl -sL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt install -y nodejs
  sudo npm install -g pm2
  ```

- [ ] **1.2.5 Configure Timezone** (10 min)
  ```bash
  sudo timedatectl set-timezone <your_timezone>
  # Example: sudo timedatectl set-timezone America/New_York
  ```

#### 1.3 AI Employee Installation (2 hours)

- [ ] **1.3.1 Clone Repository** (15 min)
  ```bash
  cd ~
  git clone https://github.com/<your_username>/hackathon_zero.git
  cd hackathon_zero
  ```

- [ ] **1.3.2 Create Cloud-Specific Branch** (10 min)
  ```bash
  git checkout -b cloud-agent
  ```

- [ ] **1.3.3 Set Up Python Virtual Environment** (15 min)
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **1.3.4 Install Playwright Browsers** (30 min)
  ```bash
  playwright install chromium
  ```

- [ ] **1.3.5 Create Cloud .env File** (30 min)
  ```bash
  cp .env.example .env.cloud
  nano .env.cloud
  ```

  **Cloud .env.cloud contents:**
  ```env
  # Cloud Agent Configuration
  AGENT_MODE=cloud
  AGENT_NAME=cloud-agent

  # Groq API (Cloud has access)
  GROQ_API_KEY=<your_groq_key>

  # Gmail (Cloud has access - read-only for triage)
  GMAIL_CREDENTIALS_PATH=/home/ubuntu/hackathon_zero/config/gmail_credentials.json

  # LinkedIn (Cloud has NO access - drafts only)
  # LINKEDIN_EMAIL=<do_not_set>
  # LINKEDIN_PASSWORD=<do_not_set>

  # Odoo (Cloud has read-only access)
  ODOO_URL=http://localhost:8069
  ODOO_DB=<db_name>
  ODOO_USERNAME=<username>
  ODOO_PASSWORD=<readonly_password>

  # Vault
  VAULT_PATH=/home/ubuntu/hackathon_zero/ai_employee_vault

  # Work-Zone Restrictions
  CLOUD_OWNS=email_triage,social_drafts,odoo_drafts
  CLOUD_FORBIDDEN=whatsapp,payments,banking,final_send
  ```

- [ ] **1.3.6 Copy Gmail Credentials (Safely)** (15 min)
  - On local machine, export Gmail credentials (read-only scope)
  - Use SCP to copy to cloud:
    ```bash
    scp -i ~/.ssh/oracle_key config/gmail_credentials_readonly.json \
      ubuntu@<VM_IP>:~/hackathon_zero/config/
    ```

- [ ] **1.3.7 Test Cloud Agent Locally** (15 min)
  ```bash
  source .env.cloud
  python -m src.orchestrator.reasoning_loop --once --agent-mode cloud
  ```

#### 1.4 PM2 Process Configuration (1 hour)

- [ ] **1.4.1 Create PM2 Ecosystem File** (30 min)
  Create `ecosystem.config.cloud.js`:
  ```javascript
  module.exports = {
    apps: [
      {
        name: 'cloud-orchestrator',
        script: 'python',
        args: '-m src.orchestrator.reasoning_loop --interval 1800 --agent-mode cloud',
        cwd: '/home/ubuntu/hackathon_zero',
        interpreter: '/home/ubuntu/hackathon_zero/.venv/bin/python',
        env: {
          AGENT_MODE: 'cloud',
          VAULT_PATH: '/home/ubuntu/hackathon_zero/ai_employee_vault'
        },
        error_file: 'logs/cloud-orchestrator-error.log',
        out_file: 'logs/cloud-orchestrator-out.log',
        time: true,
        autorestart: true,
        max_restarts: 10,
        restart_delay: 5000
      },
      {
        name: 'cloud-gmail-watcher',
        script: 'python',
        args: '-m src.watchers.gmail_watcher --agent-mode cloud --triage-only',
        cwd: '/home/ubuntu/hackathon_zero',
        interpreter: '/home/ubuntu/hackathon_zero/.venv/bin/python',
        env: {
          AGENT_MODE: 'cloud',
          VAULT_PATH: '/home/ubuntu/hackathon_zero/ai_employee_vault'
        },
        error_file: 'logs/cloud-gmail-error.log',
        out_file: 'logs/cloud-gmail-out.log',
        time: true,
        autorestart: true,
        max_restarts: 10,
        restart_delay: 5000
      },
      {
        name: 'cloud-health-monitor',
        script: 'python',
        args: '-m src.core.health_monitor --agent-mode cloud',
        cwd: '/home/ubuntu/hackathon_zero',
        interpreter: '/home/ubuntu/hackathon_zero/.venv/bin/python',
        env: {
          AGENT_MODE: 'cloud',
          VAULT_PATH: '/home/ubuntu/hackathon_zero/ai_employee_vault'
        },
        error_file: 'logs/cloud-health-error.log',
        out_file: 'logs/cloud-health-out.log',
        time: true,
        autorestart: true,
        max_restarts: 10,
        restart_delay: 5000
      }
    ]
  };
  ```

- [ ] **1.4.2 Start PM2 Processes** (15 min)
  ```bash
  pm2 start ecosystem.config.cloud.js
  pm2 save
  pm2 startup  # Follow instructions to enable auto-start on boot
  ```

- [ ] **1.4.3 Verify Processes Running** (15 min)
  ```bash
  pm2 status
  pm2 logs cloud-orchestrator --lines 50
  pm2 logs cloud-gmail-watcher --lines 50
  ```

#### 1.5 Cloud Monitoring Setup (1 hour)

- [ ] **1.5.1 Install Monitoring Tools** (20 min)
  ```bash
  sudo apt install -y nethogs iotop sysstat
  ```

- [ ] **1.5.2 Configure Log Rotation** (20 min)
  Create `/etc/logrotate.d/ai-employee`:
  ```
  /home/ubuntu/hackathon_zero/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
  }
  ```

- [ ] **1.5.3 Set Up Disk Space Monitoring** (20 min)
  Create cron job:
  ```bash
  crontab -e
  # Add:
  0 */6 * * * df -h | grep -q '9[0-9]%' && echo "Disk space critical" | mail -s "Cloud Agent Disk Alert" your@email.com
  ```

**Checkpoint:** Cloud VM running, AI Employee installed, PM2 processes operational

---

## Phase 2: Vault Sync & File-Based Delegation

**Estimated Time:** 10 hours
**Goal:** Implement git-based vault sync and claim-by-move coordination

### Tasks

#### 2.1 Vault Structure Setup (2 hours)

- [ ] **2.1.1 Update Local Vault Structure** (30 min)
  ```bash
  cd ~/hackathon_zero/ai_employee_vault

  # Create new folders
  mkdir -p In_Progress/{cloud,local}
  mkdir -p Pending_Approval/cloud/{email_drafts,social_drafts,odoo_drafts}
  mkdir -p Approved/{email_ready,social_ready,odoo_ready}
  mkdir -p Updates/cloud
  mkdir -p Signals
  ```

- [ ] **2.1.2 Create README for Each Folder** (45 min)
  Create `In_Progress/README.md`:
  ```markdown
  # In_Progress - Task Ownership

  ## Claim-by-Move Rule

  When an agent starts working on a task from Need_Action/, it MUST:
  1. Move the task file from Need_Action/<domain>/<task>.md
  2. To In_Progress/<agent>/<task>.md
  3. First agent to move owns the task
  4. Other agents MUST check In_Progress before claiming

  ## Folder Structure
  - cloud/ - Tasks claimed by Cloud Agent
  - local/ - Tasks claimed by Local Agent

  ## File Naming
  Original name preserved: EMAIL_19bb78834.md, post_draft_20260130.md

  ## Completion
  When done, move to:
  - Done/ (if completed)
  - Pending_Approval/ (if needs approval)
  - Need_Action/ (if needs re-assignment)
  ```

  Create `Pending_Approval/README.md`:
  ```markdown
  # Pending_Approval - Cloud Draft Output

  ## Purpose
  Cloud Agent writes draft actions here requiring Local approval.

  ## Folder Structure
  - cloud/email_drafts/ - Email reply drafts
  - cloud/social_drafts/ - Social post drafts
  - cloud/odoo_drafts/ - Accounting entry drafts

  ## File Format
  Each draft includes:
  - Original task reference
  - Draft content
  - Reasoning/context
  - Suggested approval actions

  ## Workflow
  1. Cloud creates draft
  2. Local reviews
  3. Local approves → moves to Approved/
  4. Local rejects → moves back to Need_Action with notes
  ```

  Create similar READMEs for other folders.

- [ ] **2.1.3 Create .gitignore for Security** (15 min)
  Update `ai_employee_vault/.gitignore`:
  ```gitignore
  # Secrets (NEVER sync)
  **/.env
  **/.env.*
  **/whatsapp_session/
  **/*_token.json
  **/*_credentials.json
  **/*.key
  **/*.pem

  # WhatsApp (Local-only, never sync)
  Need_Action/whatsapp/
  In_Progress/*/whatsapp/

  # Session data
  **/*.session
  **/cookies.json

  # Large files
  **/*.mp4
  **/*.mov
  **/*.zip
  **/*.tar.gz

  # System files
  .DS_Store
  Thumbs.db
  ```

- [ ] **2.1.4 Initialize Git Repository for Vault** (15 min)
  ```bash
  cd ~/hackathon_zero/ai_employee_vault
  git init
  git add .
  git commit -m "Initial vault structure for Platinum Tier"
  ```

- [ ] **2.1.5 Create Remote Repository** (15 min)
  - Option A: Private GitHub repo
  - Option B: Private GitLab repo
  - Option C: Self-hosted Gitea
  - Push vault:
    ```bash
    git remote add origin <your_vault_repo_url>
    git push -u origin main
    ```

#### 2.2 Claim-by-Move Implementation (3 hours)

- [ ] **2.2.1 Create Task Claim Handler** (1 hour)
  Create `src/core/task_claim_handler.py`:
  ```python
  """Task claiming system with claim-by-move rule."""

  from pathlib import Path
  import shutil
  import time
  from typing import Optional, Literal

  AgentType = Literal["cloud", "local"]

  class TaskClaimHandler:
      """Handles task claiming with atomic move operations."""

      def __init__(self, vault_path: Path, agent_name: AgentType):
          self.vault_path = Path(vault_path)
          self.agent_name = agent_name
          self.in_progress = self.vault_path / "In_Progress" / agent_name
          self.need_action = self.vault_path / "Need_Action"

      def claim_task(self, task_file: Path) -> Optional[Path]:
          """
          Claim a task from Need_Action by moving to In_Progress.

          Returns new path if successful, None if already claimed.
          """
          # Check if already claimed by someone else
          relative_path = task_file.relative_to(self.need_action)

          # Check all agents' In_Progress folders
          for agent in ["cloud", "local"]:
              other_claimed = self.vault_path / "In_Progress" / agent / relative_path.name
              if other_claimed.exists():
                  print(f"Task {task_file.name} already claimed by {agent}")
                  return None

          # Attempt atomic move (claim)
          new_path = self.in_progress / task_file.name
          try:
              shutil.move(str(task_file), str(new_path))
              print(f"✅ Claimed task: {task_file.name}")
              return new_path
          except FileNotFoundError:
              # Another agent claimed it first (race condition)
              print(f"❌ Lost race: {task_file.name} claimed by another agent")
              return None

      def release_task(self, task_file: Path, destination: Literal["done", "pending_approval", "need_action"]):
          """Release task by moving to destination."""
          if destination == "done":
              dest_path = self.vault_path / "Done" / task_file.name
          elif destination == "pending_approval":
              dest_path = self.vault_path / "Pending_Approval" / self.agent_name / task_file.name
          elif destination == "need_action":
              dest_path = self.vault_path / "Need_Action" / task_file.name

          shutil.move(str(task_file), str(dest_path))
          print(f"✅ Released task to {destination}: {task_file.name}")

      def get_my_tasks(self) -> list[Path]:
          """Get all tasks currently claimed by this agent."""
          if not self.in_progress.exists():
              return []
          return list(self.in_progress.glob("*.md"))
  ```

- [ ] **2.2.2 Create Tests for Task Claim Handler** (45 min)
  Create `tests/core/test_task_claim_handler.py`:
  ```python
  import pytest
  from pathlib import Path
  from src.core.task_claim_handler import TaskClaimHandler

  def test_claim_task_success(tmp_path):
      """Test successful task claim."""
      # Setup
      vault = tmp_path / "vault"
      need_action = vault / "Need_Action"
      in_progress = vault / "In_Progress"
      need_action.mkdir(parents=True)
      (in_progress / "cloud").mkdir(parents=True)

      task_file = need_action / "test_task.md"
      task_file.write_text("# Test Task")

      # Claim
      handler = TaskClaimHandler(vault, "cloud")
      new_path = handler.claim_task(task_file)

      assert new_path is not None
      assert new_path.exists()
      assert not task_file.exists()

  def test_claim_task_already_claimed(tmp_path):
      """Test claiming already claimed task."""
      # Setup
      vault = tmp_path / "vault"
      need_action = vault / "Need_Action"
      in_progress = vault / "In_Progress"
      need_action.mkdir(parents=True)
      (in_progress / "cloud").mkdir(parents=True)
      (in_progress / "local").mkdir(parents=True)

      task_file = need_action / "test_task.md"
      task_file.write_text("# Test Task")

      # First claim (cloud)
      handler1 = TaskClaimHandler(vault, "cloud")
      path1 = handler1.claim_task(task_file)
      assert path1 is not None

      # Simulate local trying to claim same task
      # (file already moved, so this simulates checking In_Progress)
      task_file_copy = need_action / "test_task.md"  # Would be original path
      handler2 = TaskClaimHandler(vault, "local")

      # Manually create the scenario
      # In real scenario, local would see cloud already has it
      assert (in_progress / "cloud" / "test_task.md").exists()
  ```

- [ ] **2.2.3 Integrate Claim Handler into Orchestrator** (45 min)
  Update `src/orchestrator/reasoning_loop.py`:
  ```python
  from src.core.task_claim_handler import TaskClaimHandler

  class ReasoningLoop:
      def __init__(self, ...):
          # ... existing code ...
          self.claim_handler = TaskClaimHandler(
              vault_path=self.vault_path,
              agent_name=os.getenv("AGENT_MODE", "local")  # "cloud" or "local"
          )

      def process_tasks(self):
          """Process tasks with claim-by-move."""
          # Get tasks from Need_Action
          tasks = self._scan_need_action()

          # Claim tasks one by one
          claimed_tasks = []
          for task_file in tasks:
              claimed_path = self.claim_handler.claim_task(task_file)
              if claimed_path:
                  claimed_tasks.append(claimed_path)

          # Process claimed tasks
          for task in claimed_tasks:
              self._process_single_task(task)
  ```

- [ ] **2.2.4 Test Claim-by-Move in Dual Agent Scenario** (30 min)
  - Start Cloud agent
  - Start Local agent simultaneously
  - Create 10 tasks in Need_Action
  - Verify no duplicate processing
  - Verify all tasks claimed by one agent

#### 2.3 Git Sync Automation (3 hours)

- [ ] **2.3.1 Create Vault Sync Script** (1 hour)
  Create `scripts/sync_vault.sh`:
  ```bash
  #!/bin/bash

  # Vault Git Sync Script
  # Usage: ./sync_vault.sh [cloud|local]

  set -e

  AGENT_MODE=${1:-local}
  VAULT_PATH="${VAULT_PATH:-/home/ubuntu/hackathon_zero/ai_employee_vault}"

  cd "$VAULT_PATH"

  # Pull remote changes first
  echo "📥 Pulling remote changes..."
  git pull origin main --rebase

  # Add all changes (respects .gitignore)
  echo "📝 Staging changes..."
  git add -A

  # Check if there are changes
  if git diff --staged --quiet; then
      echo "✅ No changes to sync"
      exit 0
  fi

  # Commit with agent attribution
  TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
  git commit -m "[$AGENT_MODE] Auto-sync at $TIMESTAMP"

  # Push to remote
  echo "📤 Pushing changes..."
  git push origin main

  echo "✅ Vault synced successfully"
  ```

- [ ] **2.3.2 Create Vault Sync Service** (1 hour)
  Create `src/core/vault_sync.py`:
  ```python
  """Automated vault synchronization via Git."""

  import subprocess
  import time
  from pathlib import Path
  from typing import Literal

  class VaultSyncService:
      """Handles periodic Git sync of vault."""

      def __init__(self, vault_path: Path, agent_mode: Literal["cloud", "local"], interval: int = 300):
          self.vault_path = Path(vault_path)
          self.agent_mode = agent_mode
          self.interval = interval  # seconds

      def sync_once(self) -> bool:
          """Perform one sync cycle. Returns True if successful."""
          try:
              result = subprocess.run(
                  ["./scripts/sync_vault.sh", self.agent_mode],
                  cwd=self.vault_path.parent,
                  capture_output=True,
                  text=True,
                  timeout=60
              )

              if result.returncode == 0:
                  print(f"✅ Vault synced: {result.stdout}")
                  return True
              else:
                  print(f"❌ Vault sync failed: {result.stderr}")
                  return False

          except subprocess.TimeoutExpired:
              print("❌ Vault sync timeout")
              return False
          except Exception as e:
              print(f"❌ Vault sync error: {e}")
              return False

      def sync_loop(self):
          """Run continuous sync loop."""
          print(f"🔄 Starting vault sync loop (every {self.interval}s)")

          while True:
              self.sync_once()
              time.sleep(self.interval)
  ```

- [ ] **2.3.3 Add Vault Sync to PM2** (30 min)
  Update `ecosystem.config.cloud.js`:
  ```javascript
  {
    name: 'cloud-vault-sync',
    script: 'python',
    args: '-m src.core.vault_sync --interval 300 --agent-mode cloud',
    cwd: '/home/ubuntu/hackathon_zero',
    interpreter: '/home/ubuntu/hackathon_zero/.venv/bin/python',
    env: {
      AGENT_MODE: 'cloud',
      VAULT_PATH: '/home/ubuntu/hackathon_zero/ai_employee_vault'
    },
    error_file: 'logs/cloud-vault-sync-error.log',
    out_file: 'logs/cloud-vault-sync-out.log',
    time: true,
    autorestart: true,
    max_restarts: 10,
    restart_delay: 5000
  }
  ```

- [ ] **2.3.4 Configure Git Credentials on Cloud** (30 min)
  ```bash
  # On Cloud VM
  git config --global user.name "Cloud Agent"
  git config --global user.email "cloud-agent@yourdomain.com"

  # Use Git credential helper (cache for 24 hours)
  git config --global credential.helper 'cache --timeout=86400'

  # Or use SSH keys (more secure)
  ssh-keygen -t ed25519 -C "cloud-agent@yourdomain.com"
  # Add public key to GitHub/GitLab
  ```

#### 2.4 Conflict Resolution Strategy (2 hours)

- [ ] **2.4.1 Document Conflict Resolution Rules** (30 min)
  Create `ai_employee_vault/CONFLICT_RESOLUTION.md`:
  ```markdown
  # Vault Conflict Resolution

  ## Single-Writer Files (No Conflicts)
  - Dashboard.md - Local ONLY writes
  - Updates/cloud/*.md - Cloud ONLY writes
  - In_Progress/cloud/*.md - Cloud ONLY writes
  - In_Progress/local/*.md - Local ONLY writes

  ## Append-Only Files (Auto-Resolve)
  - Logs/*.md - Both agents append (timestamped)
  - Plans/*.md - Both agents create (unique filenames)

  ## Conflict Scenarios

  ### Scenario 1: Task Double-Claim (Prevented)
  - Solution: Claim-by-move rule prevents this
  - First mover wins

  ### Scenario 2: Dashboard.md Conflict
  - Cause: Both agents modified Dashboard.md
  - Resolution: Local version ALWAYS wins
  - Cloud writes to Updates/cloud/ instead
  - Local merges Updates/ into Dashboard.md

  ### Scenario 3: Git Merge Conflict
  - Cause: Simultaneous commits
  - Resolution: Auto-resolve with "ours" strategy for single-writer files
  - Manual review for other files
  ```

- [ ] **2.4.2 Implement Auto-Resolve for Git Conflicts** (1 hour)
  Update `scripts/sync_vault.sh`:
  ```bash
  # ... existing code ...

  # Pull with auto-resolve strategy
  echo "📥 Pulling remote changes..."
  if ! git pull origin main --rebase; then
      echo "⚠️  Merge conflict detected, attempting auto-resolve..."

      # For Dashboard.md, local always wins (if local agent)
      if [ "$AGENT_MODE" = "local" ]; then
          git checkout --ours Dashboard.md 2>/dev/null || true
      elif [ "$AGENT_MODE" = "cloud" ]; then
          git checkout --theirs Dashboard.md 2>/dev/null || true
      fi

      # For single-writer folders, use ownership strategy
      # (In_Progress/cloud/ - cloud wins, etc.)
      git checkout --theirs In_Progress/cloud/* 2>/dev/null || true
      git checkout --ours In_Progress/local/* 2>/dev/null || true

      # Continue rebase
      git add -A
      git rebase --continue || true
  fi
  ```

- [ ] **2.4.3 Create Conflict Monitor** (30 min)
  Create `src/core/conflict_monitor.py`:
  ```python
  """Monitor for vault conflicts and alert."""

  def check_for_conflicts(vault_path: Path) -> list[str]:
      """Check for git conflicts in vault."""
      result = subprocess.run(
          ["git", "diff", "--name-only", "--diff-filter=U"],
          cwd=vault_path,
          capture_output=True,
          text=True
      )

      if result.returncode == 0 and result.stdout:
          conflicts = result.stdout.strip().split("\n")
          print(f"⚠️  Conflicts detected: {conflicts}")
          return conflicts

      return []
  ```

**Checkpoint:** Vault sync operational, claim-by-move working, conflicts auto-resolved

---

## Phase 3: Work-Zone Specialization

**Estimated Time:** 12 hours
**Goal:** Implement domain ownership with Cloud drafting and Local approval workflow

### Tasks

#### 3.1 Cloud Agent: Email Triage & Draft Replies (4 hours)

- [ ] **3.1.1 Create Email Triage Skill** (1.5 hours)
  Create `src/skills/communication/email_triager.py`:
  ```python
  """Email triage skill for Cloud agent - read-only analysis."""

  from ..base_skill import BaseSkill, SkillInput, SkillOutput

  class EmailTriager(BaseSkill):
      SKILL_NAME = "email_triager"
      REQUIRES_LLM = True
      DESCRIPTION = "Analyze emails and create triage reports"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """
          Triage email:
          - Urgency level
          - Action required
          - Suggested reply type
          - Related context
          """
          email = input_data.data["email"]

          # Use Groq to analyze
          prompt = f"""
          Analyze this email and provide triage information:

          From: {email['from']}
          Subject: {email['subject']}
          Body: {email['body']}

          Provide:
          1. Urgency (urgent/high/normal/low)
          2. Action required (reply/forward/file/delete)
          3. Suggested reply type (detailed/brief/acknowledge)
          4. Key points to address in reply
          5. Deadline (if any)
          """

          response = self._call_llm(prompt, model="llama-3.3-70b-versatile")

          return SkillOutput(
              result=response,
              success=True,
              metadata={"email_id": email['id']}
          )
  ```

- [ ] **3.1.2 Create Email Drafter Skill** (1.5 hours)
  Create `src/skills/communication/email_drafter.py`:
  ```python
  """Email reply drafter for Cloud agent - draft-only, no sending."""

  from ..base_skill import BaseSkill, SkillInput, SkillOutput

  class EmailDrafter(BaseSkill):
      SKILL_NAME = "email_drafter"
      REQUIRES_LLM = True
      DESCRIPTION = "Draft professional email replies"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """
          Draft email reply based on:
          - Original email
          - Company context
          - Reply type (detailed/brief/acknowledge)
          """
          email = input_data.data["email"]
          reply_type = input_data.data.get("reply_type", "professional")
          context = input_data.context.get("business_context", "")

          prompt = f"""
          Draft a {reply_type} email reply:

          ORIGINAL EMAIL:
          From: {email['from']}
          Subject: {email['subject']}
          Body: {email['body']}

          COMPANY CONTEXT:
          {context}

          REQUIREMENTS:
          - Professional tone
          - Address all key points
          - Include actionable next steps
          - Keep concise

          DRAFT REPLY:
          """

          reply_content = self._call_llm(prompt, model="llama-3.3-70b-versatile")

          # Save draft to Pending_Approval
          draft_path = self._save_draft(email, reply_content)

          return SkillOutput(
              result={"draft_path": draft_path, "content": reply_content},
              success=True
          )

      def _save_draft(self, email: dict, draft_content: str) -> str:
          """Save draft to Pending_Approval/cloud/email_drafts/"""
          draft_dir = self.vault_path / "Pending_Approval" / "cloud" / "email_drafts"
          draft_dir.mkdir(parents=True, exist_ok=True)

          # Create draft file
          draft_file = draft_dir / f"DRAFT_{email['id']}.md"
          draft_file.write_text(f"""---
  original_email_id: {email['id']}
  from: {email['from']}
  subject: RE: {email['subject']}
  created_by: cloud-agent
  created_at: {datetime.now().isoformat()}
  status: pending_approval
  ---

  # Email Reply Draft

  ## Original Email
  **From:** {email['from']}
  **Subject:** {email['subject']}

  {email['body']}

  ## Drafted Reply

  {draft_content}

  ## Actions for Local Agent
  - [ ] Review draft
  - [ ] Edit if needed
  - [ ] Approve → Move to Approved/email_ready/
  - [ ] Reject → Move back to Need_Action with notes
  """)

          return str(draft_file)
  ```

- [ ] **3.1.3 Update Cloud Gmail Watcher for Triage Mode** (1 hour)
  Update `src/watchers/gmail_watcher.py`:
  ```python
  # Add parameter for agent mode
  def __init__(self, ..., agent_mode="local", triage_only=False):
      # ... existing code ...
      self.agent_mode = agent_mode
      self.triage_only = triage_only

  def process_emails(self):
      """Process emails based on agent mode."""
      if self.agent_mode == "cloud" and self.triage_only:
          # Cloud mode: Triage + Draft only
          for email in self.get_unread_emails():
              # Triage
              triage_skill = self.registry.get_skill("email_triager")
              triage_result = triage_skill.execute(SkillInput(data={"email": email}))

              # Draft reply if action required
              if triage_result.result["action"] == "reply":
                  drafter_skill = self.registry.get_skill("email_drafter")
                  drafter_skill.execute(SkillInput(data={"email": email}))
      else:
          # Local mode: Normal processing (can send)
          # ... existing code ...
  ```

#### 3.2 Cloud Agent: Social Post Drafts (3 hours)

- [ ] **3.2.1 Create Social Post Drafter Skill** (1.5 hours)
  Create `src/skills/content/social_post_drafter.py`:
  ```python
  """Social post drafter for Cloud agent - draft-only."""

  from ..base_skill import BaseSkill, SkillInput, SkillOutput

  class SocialPostDrafter(BaseSkill):
      SKILL_NAME = "social_post_drafter"
      REQUIRES_LLM = True
      DESCRIPTION = "Draft social media posts with platform optimization"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """
          Draft social post:
          - Platform (linkedin/instagram/x)
          - Content idea
          - Tone
          - Hashtags
          """
          idea = input_data.data["idea"]
          platform = input_data.data["platform"]
          tone = input_data.data.get("tone", "professional")

          # Platform-specific guidelines
          guidelines = {
              "linkedin": "Professional, 3-5 hashtags, value-driven",
              "instagram": "Visual, 10-15 hashtags, emojis, engaging",
              "x": "Concise, 280 chars, 1-3 hashtags, punchy"
          }

          prompt = f"""
          Draft a {platform} post:

          IDEA: {idea}
          TONE: {tone}
          GUIDELINES: {guidelines[platform]}

          Create engaging content with appropriate hashtags.
          """

          draft_content = self._call_llm(prompt, model="llama-3.3-70b-versatile")

          # Save draft
          draft_path = self._save_draft(platform, draft_content, idea)

          return SkillOutput(
              result={"draft_path": draft_path, "content": draft_content},
              success=True
          )

      def _save_draft(self, platform: str, content: str, idea: str) -> str:
          """Save to Pending_Approval/cloud/social_drafts/"""
          draft_dir = self.vault_path / "Pending_Approval" / "cloud" / "social_drafts"
          draft_dir.mkdir(parents=True, exist_ok=True)

          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          draft_file = draft_dir / f"{platform}_draft_{timestamp}.md"

          draft_file.write_text(f"""---
  platform: {platform}
  idea: {idea}
  created_by: cloud-agent
  created_at: {datetime.now().isoformat()}
  status: pending_approval
  image_path: null
  ---

  # {platform.capitalize()} Post Draft

  {content}

  ## Actions for Local Agent
  - [ ] Review content
  - [ ] Add image if needed
  - [ ] Approve → Move to Approved/social_ready/{platform}/
  - [ ] Reject → Edit or discard
  """)

          return str(draft_file)
  ```

- [ ] **3.2.2 Create Social Post Scheduler** (1 hour)
  Create `src/skills/planning/social_scheduler.py`:
  ```python
  """Social post scheduling for Cloud agent - draft calendar."""

  class SocialScheduler(BaseSkill):
      SKILL_NAME = "social_scheduler"
      REQUIRES_LLM = True
      DESCRIPTION = "Create social media content calendar"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """
          Generate posting schedule:
          - Best times per platform
          - Content themes
          - Frequency recommendations
          """
          goals = input_data.data.get("goals", "")

          prompt = f"""
          Create a 7-day social media content calendar:

          GOALS: {goals}

          For each day, suggest:
          - Platform (LinkedIn/Instagram/X)
          - Post topic/theme
          - Best time to post
          - Content type (text/image/video)

          Format as structured schedule.
          """

          schedule = self._call_llm(prompt, model="llama-3.3-70b-versatile")

          # Save to Pending_Approval for review
          schedule_path = self._save_schedule(schedule)

          return SkillOutput(result={"schedule_path": schedule_path}, success=True)
  ```

- [ ] **3.2.3 Test Cloud Social Drafting Workflow** (30 min)
  - Manually create content idea in Need_Action/social_posts/
  - Run Cloud orchestrator
  - Verify draft created in Pending_Approval/cloud/social_drafts/
  - Verify Cloud did NOT post directly

#### 3.3 Local Agent: Approval Workflow (3 hours)

- [ ] **3.3.1 Create Approval Handler** (1.5 hours)
  Create `src/core/approval_handler.py`:
  ```python
  """Approval workflow for Local agent."""

  from pathlib import Path
  import shutil
  from typing import Literal

  ApprovalAction = Literal["approve", "reject", "edit"]

  class ApprovalHandler:
      """Handle approval workflow for Cloud-drafted items."""

      def __init__(self, vault_path: Path):
          self.vault_path = Path(vault_path)
          self.pending = self.vault_path / "Pending_Approval" / "cloud"
          self.approved = self.vault_path / "Approved"

      def list_pending_approvals(self) -> dict[str, list[Path]]:
          """List all items pending approval by category."""
          pending = {
              "email_drafts": list((self.pending / "email_drafts").glob("*.md")),
              "social_drafts": list((self.pending / "social_drafts").glob("*.md")),
              "odoo_drafts": list((self.pending / "odoo_drafts").glob("*.md"))
          }
          return pending

      def approve_email_draft(self, draft_file: Path):
          """Approve email draft → move to Approved/email_ready/"""
          dest = self.approved / "email_ready" / draft_file.name
          dest.parent.mkdir(parents=True, exist_ok=True)
          shutil.move(str(draft_file), str(dest))
          print(f"✅ Approved email draft: {draft_file.name}")

      def approve_social_draft(self, draft_file: Path, platform: str):
          """Approve social draft → move to Approved/social_ready/{platform}/"""
          dest = self.approved / "social_ready" / platform / draft_file.name
          dest.parent.mkdir(parents=True, exist_ok=True)
          shutil.move(str(draft_file), str(dest))
          print(f"✅ Approved social draft for {platform}: {draft_file.name}")

      def reject_draft(self, draft_file: Path, reason: str):
          """Reject draft → move back to Need_Action with rejection reason."""
          # Add rejection note
          content = draft_file.read_text()
          rejection_note = f"\n\n## REJECTED\n\n**Reason:** {reason}\n**Date:** {datetime.now().isoformat()}\n"
          updated_content = content + rejection_note
          draft_file.write_text(updated_content)

          # Move to Need_Action
          dest = self.vault_path / "Need_Action" / "rejected" / draft_file.name
          dest.parent.mkdir(parents=True, exist_ok=True)
          shutil.move(str(draft_file), str(dest))
          print(f"❌ Rejected draft: {draft_file.name}")

      def edit_draft(self, draft_file: Path, new_content: str):
          """Edit draft and keep in pending for re-review."""
          draft_file.write_text(new_content)
          print(f"✏️  Edited draft: {draft_file.name}")
  ```

- [ ] **3.3.2 Create Approval CLI Tool** (1 hour)
  Create `scripts/approve.py`:
  ```python
  """CLI tool for Local agent to approve Cloud drafts."""

  import click
  from pathlib import Path
  from src.core.approval_handler import ApprovalHandler

  @click.group()
  def cli():
      """Approval management CLI."""
      pass

  @cli.command()
  def list():
      """List all pending approvals."""
      handler = ApprovalHandler(Path("ai_employee_vault"))
      pending = handler.list_pending_approvals()

      for category, files in pending.items():
          click.echo(f"\n{category.upper()} ({len(files)} items):")
          for i, file in enumerate(files, 1):
              click.echo(f"  {i}. {file.name}")

  @cli.command()
  @click.argument('draft_file')
  @click.option('--category', type=click.Choice(['email', 'social', 'odoo']))
  def approve(draft_file, category):
      """Approve a draft."""
      handler = ApprovalHandler(Path("ai_employee_vault"))
      file_path = Path(draft_file)

      if category == 'email':
          handler.approve_email_draft(file_path)
      elif category == 'social':
          # Parse platform from filename or frontmatter
          platform = file_path.stem.split('_')[0]
          handler.approve_social_draft(file_path, platform)

      click.echo(f"✅ Approved: {draft_file}")

  @cli.command()
  @click.argument('draft_file')
  @click.argument('reason')
  def reject(draft_file, reason):
      """Reject a draft."""
      handler = ApprovalHandler(Path("ai_employee_vault"))
      handler.reject_draft(Path(draft_file), reason)
      click.echo(f"❌ Rejected: {draft_file}")

  if __name__ == "__main__":
      cli()
  ```

- [ ] **3.3.3 Test Approval Workflow End-to-End** (30 min)
  ```bash
  # List pending
  python scripts/approve.py list

  # Approve email draft
  python scripts/approve.py approve \
    ai_employee_vault/Pending_Approval/cloud/email_drafts/DRAFT_123.md \
    --category email

  # Reject social draft
  python scripts/approve.py reject \
    ai_employee_vault/Pending_Approval/cloud/social_drafts/linkedin_draft_123.md \
    "Tone too casual for our brand"
  ```

#### 3.4 Local Agent: Final Execution (2 hours)

- [ ] **3.4.1 Update Local Email Sender** (45 min)
  Update `src/watchers/gmail_watcher.py`:
  ```python
  def execute_approved_emails(self):
      """Local agent sends approved email drafts."""
      approved_dir = self.vault_path / "Approved" / "email_ready"

      for draft_file in approved_dir.glob("*.md"):
          # Parse draft
          email_data = self._parse_email_draft(draft_file)

          # Send via Gmail API
          sent = self._send_email(
              to=email_data['to'],
              subject=email_data['subject'],
              body=email_data['body']
          )

          if sent:
              # Move to Done
              done_path = self.vault_path / "Done" / draft_file.name
              shutil.move(str(draft_file), str(done_path))

              # Log
              self._log_action("email_sent", email_data)
  ```

- [ ] **3.4.2 Update Local Social Posters** (45 min)
  Update `src/watchers/linkedin_watcher.py`, `insta_watcher.py`, `x_watcher.py`:
  ```python
  def execute_approved_posts(self):
      """Local agent posts approved social content."""
      approved_dir = self.vault_path / "Approved" / "social_ready" / self.platform

      for post_file in approved_dir.glob("*.md"):
          # Parse post
          post_data = self._parse_post(post_file)

          # Post to platform
          posted = self._post_to_platform(
              content=post_data['content'],
              image=post_data.get('image_path')
          )

          if posted:
              # Move to Done
              done_path = self.vault_path / "Done" / post_file.name
              shutil.move(str(post_file), str(done_path))

              # Log
              self._log_action("social_posted", post_data)
  ```

- [ ] **3.4.3 Test Full Cloud→Local Workflow** (30 min)
  1. Cloud drafts email reply
  2. Cloud saves to Pending_Approval/cloud/email_drafts/
  3. Git sync runs
  4. Local sees pending draft
  5. User runs: `python scripts/approve.py approve ...`
  6. Draft moves to Approved/email_ready/
  7. Local Gmail watcher sends email
  8. Email moves to Done/
  9. Git sync runs
  10. Cloud sees completed task in Done/

**Checkpoint:** Work-zone specialization working, Cloud drafts, Local approves and executes

---

## Phase 4: Cloud Odoo Deployment

**Estimated Time:** 10 hours
**Goal:** Deploy Odoo Community 24/7 on Cloud VM with HTTPS, backups, MCP integration

### Tasks

#### 4.1 Odoo Installation (3 hours)

- [ ] **4.1.1 Install PostgreSQL** (30 min)
  ```bash
  sudo apt install -y postgresql postgresql-contrib
  sudo systemctl enable postgresql
  sudo systemctl start postgresql

  # Create Odoo database user
  sudo -u postgres createuser -s odoo
  sudo -u postgres psql -c "ALTER USER odoo WITH PASSWORD 'strong_password_here';"
  ```

- [ ] **4.1.2 Install Odoo Dependencies** (45 min)
  ```bash
  sudo apt install -y python3-pip python3-dev libxml2-dev libxslt1-dev \
    libldap2-dev libsasl2-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev \
    zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev \
    libfribidi-dev libxcb1-dev libpq-dev node-less
  ```

- [ ] **4.1.3 Download and Install Odoo** (1 hour)
  ```bash
  sudo useradd -m -U -r -d /opt/odoo -s /bin/bash odoo
  sudo -u odoo git clone https://www.github.com/odoo/odoo --depth 1 \
    --branch 17.0 /opt/odoo/odoo

  cd /opt/odoo
  sudo -u odoo python3 -m venv venv
  sudo -u odoo venv/bin/pip install wheel
  sudo -u odoo venv/bin/pip install -r odoo/requirements.txt
  ```

- [ ] **4.1.4 Configure Odoo** (45 min)
  Create `/etc/odoo.conf`:
  ```ini
  [options]
  admin_passwd = admin_master_password_change_this
  db_host = localhost
  db_port = 5432
  db_user = odoo
  db_password = strong_password_here
  addons_path = /opt/odoo/odoo/addons
  http_port = 8069
  logfile = /var/log/odoo/odoo.log
  log_level = info

  # Performance
  workers = 2
  max_cron_threads = 1
  limit_memory_hard = 2684354560
  limit_memory_soft = 2147483648
  limit_request = 8192
  limit_time_cpu = 600
  limit_time_real = 1200
  ```

  Create systemd service `/etc/systemd/system/odoo.service`:
  ```ini
  [Unit]
  Description=Odoo
  After=network.target postgresql.service

  [Service]
  Type=simple
  User=odoo
  Group=odoo
  ExecStart=/opt/odoo/venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf
  StandardOutput=journal+console

  [Install]
  WantedBy=multi-user.target
  ```

  Start Odoo:
  ```bash
  sudo mkdir /var/log/odoo
  sudo chown odoo:odoo /var/log/odoo
  sudo systemctl daemon-reload
  sudo systemctl enable odoo
  sudo systemctl start odoo
  ```

#### 4.2 HTTPS Setup (2 hours)

- [ ] **4.2.1 Install Nginx** (20 min)
  ```bash
  sudo apt install -y nginx
  sudo systemctl enable nginx
  ```

- [ ] **4.2.2 Install Certbot** (20 min)
  ```bash
  sudo apt install -y certbot python3-certbot-nginx
  ```

- [ ] **4.2.3 Configure Domain** (30 min)
  - Register domain or use subdomain: `odoo.yourdomain.com`
  - Point A record to Cloud VM public IP
  - Wait for DNS propagation (5-30 min)

- [ ] **4.2.4 Configure Nginx Reverse Proxy** (30 min)
  Create `/etc/nginx/sites-available/odoo`:
  ```nginx
  upstream odoo {
      server 127.0.0.1:8069;
  }

  server {
      listen 80;
      server_name odoo.yourdomain.com;

      location / {
          return 301 https://$host$request_uri;
      }
  }

  server {
      listen 443 ssl http2;
      server_name odoo.yourdomain.com;

      # SSL certificates (will be added by certbot)

      client_max_body_size 100M;

      location / {
          proxy_pass http://odoo;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }

      location /longpolling {
          proxy_pass http://odoo;
      }
  }
  ```

  Enable site:
  ```bash
  sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl restart nginx
  ```

- [ ] **4.2.5 Get SSL Certificate** (20 min)
  ```bash
  sudo certbot --nginx -d odoo.yourdomain.com
  # Follow prompts
  ```

#### 4.3 Odoo Database Setup (1 hour)

- [ ] **4.3.1 Create Odoo Database** (20 min)
  - Visit https://odoo.yourdomain.com
  - Create database: `ai_employee_accounting`
  - Set admin password
  - Choose apps: Accounting, Invoicing, Contacts

- [ ] **4.3.2 Configure Odoo for AI Employee** (20 min)
  - Create API user: `cloud_agent` (read-only)
  - Create API user: `local_agent` (read-write)
  - Generate API keys
  - Configure accounting defaults

- [ ] **4.3.3 Test Odoo API Access** (20 min)
  ```python
  import xmlrpc.client

  url = "https://odoo.yourdomain.com"
  db = "ai_employee_accounting"
  username = "cloud_agent"
  password = "api_key_here"

  common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
  uid = common.authenticate(db, username, password, {})

  models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
  # Test read
  partners = models.execute_kw(db, uid, password,
      'res.partner', 'search_read',
      [[['is_company', '=', True]]],
      {'fields': ['name', 'email'], 'limit': 5})

  print(partners)
  ```

#### 4.4 Odoo MCP Server Integration (2 hours)

- [ ] **4.4.1 Update Odoo MCP Server Config** (30 min)
  Update `src/mcp_servers/odoo/config.py`:
  ```python
  # Cloud agent - read-only
  if os.getenv("AGENT_MODE") == "cloud":
      ODOO_URL = "https://odoo.yourdomain.com"
      ODOO_DB = "ai_employee_accounting"
      ODOO_USER = "cloud_agent"
      ODOO_PASSWORD = os.getenv("ODOO_CLOUD_PASSWORD")
      READ_ONLY = True
  # Local agent - read-write
  else:
      ODOO_URL = "https://odoo.yourdomain.com"
      ODOO_DB = "ai_employee_accounting"
      ODOO_USER = "local_agent"
      ODOO_PASSWORD = os.getenv("ODOO_LOCAL_PASSWORD")
      READ_ONLY = False
  ```

- [ ] **4.4.2 Create Odoo Draft Generator Skill** (1 hour)
  Create `src/skills/accounting/odoo_draft_generator.py`:
  ```python
  """Odoo draft generator for Cloud agent."""

  class OdooDraftGenerator(BaseSkill):
      SKILL_NAME = "odoo_draft_generator"
      REQUIRES_LLM = True
      DESCRIPTION = "Generate draft accounting entries for Odoo"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """
          Generate draft:
          - Invoice
          - Payment
          - Journal entry
          """
          entry_type = input_data.data["type"]
          details = input_data.data["details"]

          # Use LLM to structure entry
          prompt = f"""
          Create a draft Odoo {entry_type} entry:

          DETAILS:
          {details}

          Provide structured data:
          - Partner
          - Amount
          - Description
          - Account codes
          - Payment terms
          """

          draft_data = self._call_llm(prompt)

          # Save to Pending_Approval/cloud/odoo_drafts/
          draft_path = self._save_odoo_draft(entry_type, draft_data)

          return SkillOutput(result={"draft_path": draft_path}, success=True)
  ```

- [ ] **4.4.3 Create Odoo Poster for Local Agent** (30 min)
  Create `src/skills/accounting/odoo_poster.py`:
  ```python
  """Odoo poster for Local agent - final execution."""

  class OdooPoster(BaseSkill):
      SKILL_NAME = "odoo_poster"
      REQUIRES_LLM = False
      DESCRIPTION = "Post approved accounting entries to Odoo"

      def execute(self, input_data: SkillInput) -> SkillOutput:
          """Post approved entry to Odoo via MCP."""
          draft_data = input_data.data["draft"]
          entry_type = input_data.data["type"]

          # Call Odoo MCP server
          if entry_type == "invoice":
              result = self._post_invoice(draft_data)
          elif entry_type == "payment":
              result = self._post_payment(draft_data)

          return SkillOutput(result=result, success=True)

      def _post_invoice(self, draft_data: dict):
          """Post invoice via MCP."""
          # Use MCP server to create invoice
          mcp_client = MCPClient("odoo")
          invoice_id = mcp_client.call("create_invoice", draft_data)
          return {"invoice_id": invoice_id}
  ```

#### 4.5 Odoo Backup Strategy (2 hours)

- [ ] **4.5.1 Create Backup Script** (45 min)
  Create `/opt/odoo/backup.sh`:
  ```bash
  #!/bin/bash

  BACKUP_DIR="/opt/odoo/backups"
  DATE=$(date +%Y%m%d_%H%M%S)
  DB_NAME="ai_employee_accounting"

  mkdir -p "$BACKUP_DIR"

  # Backup database
  sudo -u postgres pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"

  # Backup filestore
  tar -czf "$BACKUP_DIR/filestore_${DATE}.tar.gz" /opt/odoo/.local/share/Odoo/filestore/

  # Keep only last 7 days
  find "$BACKUP_DIR" -type f -mtime +7 -delete

  echo "Backup completed: $DATE"
  ```

- [ ] **4.5.2 Schedule Automated Backups** (15 min)
  ```bash
  sudo crontab -e
  # Add:
  0 2 * * * /opt/odoo/backup.sh >> /var/log/odoo/backup.log 2>&1
  ```

- [ ] **4.5.3 Set Up Off-Site Backup** (1 hour)
  - Option A: S3/Oracle Object Storage
  - Option B: Rsync to another server
  - Option C: Cloud backup service

  Example S3 sync:
  ```bash
  # Install AWS CLI
  sudo apt install -y awscli

  # Configure credentials
  aws configure

  # Add to backup script
  aws s3 sync "$BACKUP_DIR" s3://your-bucket/odoo-backups/
  ```

**Checkpoint:** Odoo 24/7 on Cloud, HTTPS working, MCP integrated, backups automated

---

## Phase 5: Security & Secrets Management

**Estimated Time:** 6 hours
**Goal:** Ensure secrets never sync, Cloud has minimal credentials, audit all access

### Tasks

#### 5.1 Secrets Audit (2 hours)

- [ ] **5.1.1 Inventory All Secrets** (30 min)
  Create `SECRETS_INVENTORY.md`:
  ```markdown
  # Secrets Inventory

  ## Cloud Agent (Minimal Access)
  - GROQ_API_KEY (AI reasoning)
  - GMAIL_CREDENTIALS (read-only scope)
  - ODOO_CLOUD_PASSWORD (read-only user)

  ## Local Agent (Full Access)
  - GROQ_API_KEY
  - GMAIL_CREDENTIALS (full scope)
  - LINKEDIN_EMAIL + LINKEDIN_PASSWORD
  - INSTAGRAM_USERNAME + INSTAGRAM_PASSWORD
  - X_USERNAME + X_PASSWORD
  - WHATSAPP_SESSION (file-based)
  - ODOO_LOCAL_PASSWORD (read-write user)
  - PAYMENT_API_KEYS (Stripe, PayPal, etc.)
  - BANKING_CREDENTIALS

  ## Never Synced
  - .env files
  - whatsapp_session/
  - *_token.json
  - *_credentials.json
  - *.key, *.pem
  ```

- [ ] **5.1.2 Verify .gitignore Coverage** (30 min)
  ```bash
  # Test that secrets are ignored
  cd ai_employee_vault

  # Create test secret files
  echo "secret" > .env.test
  echo "secret" > whatsapp_session/test.txt
  echo "secret" > gmail_token.json

  # Check git status
  git status  # Should NOT show test files

  # Clean up
  rm .env.test whatsapp_session/test.txt gmail_token.json
  ```

- [ ] **5.1.3 Audit Cloud VM for Leaked Secrets** (1 hour)
  ```bash
  # On Cloud VM
  cd ~/hackathon_zero

  # Search for potential secrets in vault
  grep -r "password" ai_employee_vault/ || echo "None found"
  grep -r "api_key" ai_employee_vault/ || echo "None found"
  grep -r "token" ai_employee_vault/ || echo "None found"

  # Check .env.cloud has ONLY allowed secrets
  cat .env.cloud | grep -E "(WHATSAPP|PAYMENT|BANKING)" && echo "SECURITY VIOLATION" || echo "OK"
  ```

#### 5.2 Gmail Scope Restriction (1 hour)

- [ ] **5.2.1 Create Read-Only Gmail Credentials** (30 min)
  - Go to Google Cloud Console
  - Create new OAuth2 credentials
  - Scopes: `gmail.readonly`, `gmail.metadata`
  - Download as `gmail_credentials_readonly.json`
  - Test:
    ```python
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_file('gmail_credentials_readonly.json')
    # Try to send email - should fail
    ```

- [ ] **5.2.2 Update Cloud Gmail Watcher** (30 min)
  ```python
  # src/watchers/gmail_watcher.py
  def __init__(self, ..., agent_mode="local"):
      if agent_mode == "cloud":
          # Use read-only credentials
          self.credentials_path = "config/gmail_credentials_readonly.json"
          self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
      else:
          # Use full credentials
          self.credentials_path = "config/gmail_credentials.json"
          self.scopes = ['https://www.googleapis.com/auth/gmail.modify']
  ```

#### 5.3 Odoo Permission Separation (1 hour)

- [ ] **5.3.1 Create Odoo Read-Only User** (30 min)
  In Odoo:
  1. Settings → Users → Create
  2. Name: Cloud Agent
  3. Login: cloud_agent
  4. Access Rights:
     - Accounting: Read-only
     - Contacts: Read-only
     - Sales: Read-only
  5. Save password

- [ ] **5.3.2 Test Permission Separation** (30 min)
  ```python
  # Test Cloud agent (read-only)
  cloud_client = OdooClient(user="cloud_agent", password="...")

  # Should succeed
  partners = cloud_client.search_read('res.partner', [], ['name'])

  # Should fail
  try:
      cloud_client.create('account.move', {'partner_id': 1})
      print("SECURITY VIOLATION - Cloud can write!")
  except PermissionError:
      print("✅ Cloud correctly restricted")

  # Test Local agent (read-write)
  local_client = OdooClient(user="local_agent", password="...")

  # Should succeed
  invoice_id = local_client.create('account.move', {...})
  print(f"✅ Local can write: {invoice_id}")
  ```

#### 5.4 Audit Logging Enhancement (2 hours)

- [ ] **5.4.1 Add Agent Attribution to Logs** (1 hour)
  Update `src/logging/audit_logger.py`:
  ```python
  def log_action(self, action: str, data: dict):
      """Log action with agent attribution."""
      log_entry = {
          "timestamp": datetime.now().isoformat(),
          "agent": os.getenv("AGENT_MODE", "local"),
          "agent_name": os.getenv("AGENT_NAME", "unknown"),
          "action": action,
          "data": data,
          "vault_synced": self._is_vault_synced()
      }

      # Write to Logs/audit.jsonl
      with open(self.vault_path / "Logs" / "audit.jsonl", "a") as f:
          f.write(json.dumps(log_entry) + "\n")
  ```

- [ ] **5.4.2 Create Security Audit Report Generator** (1 hour)
  Create `scripts/security_audit.py`:
  ```python
  """Generate security audit report."""

  def generate_report(vault_path: Path):
      """Analyze audit logs for security issues."""
      logs = []
      with open(vault_path / "Logs" / "audit.jsonl") as f:
          for line in f:
              logs.append(json.loads(line))

      # Check for violations
      violations = []

      # 1. Cloud attempting final actions
      cloud_sends = [l for l in logs if l['agent'] == 'cloud' and l['action'] in ['email_sent', 'social_posted', 'payment_executed']]
      if cloud_sends:
          violations.append(f"Cloud attempted {len(cloud_sends)} final actions")

      # 2. Local accessing WhatsApp from wrong machine
      # 3. Suspicious timing patterns
      # etc.

      # Generate report
      report = f"""
      # Security Audit Report

      Generated: {datetime.now()}

      ## Summary
      - Total actions: {len(logs)}
      - Cloud actions: {len([l for l in logs if l['agent'] == 'cloud'])}
      - Local actions: {len([l for l in logs if l['agent'] == 'local'])}

      ## Violations
      {violations}

      ## Recommendations
      ...
      """

      return report
  ```

**Checkpoint:** Secrets secured, permissions enforced, audit logging complete

---

## Phase 6: Health Monitoring & Always-On Operations

**Estimated Time:** 8 hours
**Goal:** Implement health checks, alerting, auto-recovery, uptime monitoring

### Tasks

#### 6.1 Health Monitor Service (3 hours)

- [ ] **6.1.1 Create Health Monitor** (1.5 hours)
  Create `src/core/health_monitor.py`:
  ```python
  """Health monitoring for AI Employee agents."""

  from dataclasses import dataclass
  from datetime import datetime, timedelta
  from typing import Literal
  import psutil
  import subprocess

  @dataclass
  class HealthStatus:
      timestamp: datetime
      agent_mode: Literal["cloud", "local"]
      status: Literal["healthy", "degraded", "critical"]
      checks: dict[str, bool]
      metrics: dict[str, float]
      issues: list[str]

  class HealthMonitor:
      """Monitor agent health and system resources."""

      def __init__(self, vault_path: Path, agent_mode: str):
          self.vault_path = Path(vault_path)
          self.agent_mode = agent_mode

      def check_health(self) -> HealthStatus:
          """Perform comprehensive health check."""
          checks = {}
          metrics = {}
          issues = []

          # 1. Vault accessibility
          checks['vault_accessible'] = self.vault_path.exists()
          if not checks['vault_accessible']:
              issues.append("Vault directory not accessible")

          # 2. Git sync health
          checks['git_synced'] = self._check_git_sync()
          if not checks['git_synced']:
              issues.append("Vault not synced in last 10 minutes")

          # 3. PM2 processes (Cloud only)
          if self.agent_mode == "cloud":
              checks['pm2_running'] = self._check_pm2_processes()
              if not checks['pm2_running']:
                  issues.append("PM2 processes not running")

          # 4. Disk space
          disk = psutil.disk_usage('/')
          metrics['disk_usage_percent'] = disk.percent
          checks['disk_ok'] = disk.percent < 90
          if not checks['disk_ok']:
              issues.append(f"Disk usage critical: {disk.percent}%")

          # 5. Memory usage
          mem = psutil.virtual_memory()
          metrics['memory_usage_percent'] = mem.percent
          checks['memory_ok'] = mem.percent < 90
          if not checks['memory_ok']:
              issues.append(f"Memory usage high: {mem.percent}%")

          # 6. Recent activity
          checks['recent_activity'] = self._check_recent_activity()
          if not checks['recent_activity']:
              issues.append("No agent activity in last hour")

          # 7. Odoo reachability (Cloud)
          if self.agent_mode == "cloud":
              checks['odoo_reachable'] = self._check_odoo()
              if not checks['odoo_reachable']:
                  issues.append("Odoo not reachable")

          # Determine overall status
          if all(checks.values()):
              status = "healthy"
          elif any(not v for k, v in checks.items() if k in ['vault_accessible', 'disk_ok']):
              status = "critical"
          else:
              status = "degraded"

          return HealthStatus(
              timestamp=datetime.now(),
              agent_mode=self.agent_mode,
              status=status,
              checks=checks,
              metrics=metrics,
              issues=issues
          )

      def _check_git_sync(self) -> bool:
          """Check if vault synced recently."""
          try:
              result = subprocess.run(
                  ["git", "log", "-1", "--format=%ct"],
                  cwd=self.vault_path,
                  capture_output=True,
                  text=True
              )
              last_commit = int(result.stdout.strip())
              return (time.time() - last_commit) < 600  # Last 10 min
          except:
              return False

      def _check_pm2_processes(self) -> bool:
          """Check PM2 processes are running."""
          try:
              result = subprocess.run(
                  ["pm2", "jlist"],
                  capture_output=True,
                  text=True
              )
              processes = json.loads(result.stdout)
              return all(p['pm2_env']['status'] == 'online' for p in processes)
          except:
              return False

      def _check_recent_activity(self) -> bool:
          """Check for recent agent activity in logs."""
          try:
              log_files = sorted(
                  (self.vault_path / "Logs").glob("*.jsonl"),
                  key=lambda p: p.stat().st_mtime,
                  reverse=True
              )
              if not log_files:
                  return False

              latest_log = log_files[0]
              modified_time = datetime.fromtimestamp(latest_log.stat().st_mtime)
              return (datetime.now() - modified_time) < timedelta(hours=1)
          except:
              return False

      def _check_odoo(self) -> bool:
          """Check Odoo reachability."""
          try:
              response = requests.get(
                  os.getenv("ODOO_URL", "http://localhost:8069"),
                  timeout=5
              )
              return response.status_code == 200
          except:
              return False
  ```

- [ ] **6.1.2 Create Health Check CLI** (30 min)
  Create `scripts/health_check.py`:
  ```python
  """CLI for health checks."""

  import click
  from src.core.health_monitor import HealthMonitor

  @click.command()
  @click.option('--agent-mode', default='local', type=click.Choice(['cloud', 'local']))
  def check(agent_mode):
      """Run health check."""
      monitor = HealthMonitor(Path("ai_employee_vault"), agent_mode)
      status = monitor.check_health()

      # Print status
      emoji = {"healthy": "✅", "degraded": "⚠️", "critical": "❌"}[status.status]
      click.echo(f"\n{emoji} Status: {status.status.upper()}")

      click.echo("\nChecks:")
      for check, passed in status.checks.items():
          icon = "✅" if passed else "❌"
          click.echo(f"  {icon} {check}")

      click.echo("\nMetrics:")
      for metric, value in status.metrics.items():
          click.echo(f"  {metric}: {value:.1f}")

      if status.issues:
          click.echo("\nIssues:")
          for issue in status.issues:
              click.echo(f"  ❌ {issue}")

      # Exit code
      exit_codes = {"healthy": 0, "degraded": 1, "critical": 2}
      sys.exit(exit_codes[status.status])

  if __name__ == "__main__":
      check()
  ```

- [ ] **6.1.3 Add Health Monitor to PM2** (1 hour)
  Update `ecosystem.config.cloud.js`:
  ```javascript
  {
    name: 'cloud-health-monitor',
    script: 'python',
    args: '-m src.core.health_monitor --agent-mode cloud --interval 300',
    cwd: '/home/ubuntu/hackathon_zero',
    interpreter: '/home/ubuntu/hackathon_zero/.venv/bin/python',
    error_file: 'logs/health-monitor-error.log',
    out_file: 'logs/health-monitor-out.log',
    time: true,
    autorestart: true,
    max_restarts: 10,
    restart_delay: 5000
  }
  ```

#### 6.2 Alerting System (2 hours)

- [ ] **6.2.1 Create Alert Handler** (1 hour)
  Create `src/core/alert_handler.py`:
  ```python
  """Alert system for critical issues."""

  from enum import Enum
  from dataclasses import dataclass

  class AlertSeverity(Enum):
      INFO = "info"
      WARNING = "warning"
      CRITICAL = "critical"

  @dataclass
  class Alert:
      severity: AlertSeverity
      title: str
      message: str
      timestamp: datetime
      agent_mode: str

  class AlertHandler:
      """Send alerts via multiple channels."""

      def __init__(self, agent_mode: str):
          self.agent_mode = agent_mode
          self.alert_email = os.getenv("ALERT_EMAIL")
          self.alert_webhook = os.getenv("ALERT_WEBHOOK")  # Slack, Discord, etc.

      def send_alert(self, alert: Alert):
          """Send alert via configured channels."""
          # Email
          if self.alert_email:
              self._send_email_alert(alert)

          # Webhook (Slack/Discord)
          if self.alert_webhook:
              self._send_webhook_alert(alert)

          # Log to file
          self._log_alert(alert)

      def _send_email_alert(self, alert: Alert):
          """Send alert via email."""
          # Use Gmail API or SMTP
          pass

      def _send_webhook_alert(self, alert: Alert):
          """Send alert to webhook."""
          payload = {
              "text": f"[{alert.severity.value.upper()}] {alert.title}",
              "blocks": [
                  {"type": "section", "text": {"type": "mrkdwn", "text": alert.message}}
              ]
          }
          requests.post(self.alert_webhook, json=payload)

      def _log_alert(self, alert: Alert):
          """Log alert to file."""
          with open("logs/alerts.jsonl", "a") as f:
              f.write(json.dumps(dataclasses.asdict(alert), default=str) + "\n")
  ```

- [ ] **6.2.2 Integrate Alerts with Health Monitor** (30 min)
  Update `src/core/health_monitor.py`:
  ```python
  from src.core.alert_handler import AlertHandler, Alert, AlertSeverity

  class HealthMonitor:
      def __init__(self, ...):
          # ... existing code ...
          self.alert_handler = AlertHandler(agent_mode)
          self.last_alert_time = {}

      def check_health(self) -> HealthStatus:
          status = ...  # existing check

          # Send alerts for issues
          if status.status == "critical":
              self._send_alert(
                  AlertSeverity.CRITICAL,
                  f"{self.agent_mode.capitalize()} Agent Critical",
                  "\n".join(status.issues)
              )
          elif status.status == "degraded":
              self._send_alert(
                  AlertSeverity.WARNING,
                  f"{self.agent_mode.capitalize()} Agent Degraded",
                  "\n".join(status.issues)
              )

          return status

      def _send_alert(self, severity: AlertSeverity, title: str, message: str):
          """Send alert with rate limiting."""
          # Don't spam alerts - once per hour per issue
          alert_key = f"{severity.value}_{title}"
          last_time = self.last_alert_time.get(alert_key, 0)

          if time.time() - last_time > 3600:  # 1 hour
              alert = Alert(
                  severity=severity,
                  title=title,
                  message=message,
                  timestamp=datetime.now(),
                  agent_mode=self.agent_mode
              )
              self.alert_handler.send_alert(alert)
              self.last_alert_time[alert_key] = time.time()
  ```

- [ ] **6.2.3 Configure Alert Channels** (30 min)
  Add to `.env.cloud`:
  ```env
  # Alerts
  ALERT_EMAIL=your@email.com
  ALERT_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  ```

#### 6.3 Auto-Recovery (2 hours)

- [ ] **6.3.1 Create Recovery Handler** (1 hour)
  Create `src/core/recovery_handler.py`:
  ```python
  """Automatic recovery from common failures."""

  class RecoveryHandler:
      """Handle automatic recovery."""

      def __init__(self, vault_path: Path, agent_mode: str):
          self.vault_path = Path(vault_path)
          self.agent_mode = agent_mode

      def attempt_recovery(self, health_status: HealthStatus) -> bool:
          """Attempt to recover from issues."""
          recovered = True

          for issue in health_status.issues:
              if "Vault not synced" in issue:
                  recovered &= self._recover_vault_sync()
              elif "PM2 processes not running" in issue:
                  recovered &= self._recover_pm2_processes()
              elif "Disk usage critical" in issue:
                  recovered &= self._recover_disk_space()

          return recovered

      def _recover_vault_sync(self) -> bool:
          """Attempt to fix vault sync."""
          try:
              # Force sync
              subprocess.run(
                  ["./scripts/sync_vault.sh", self.agent_mode],
                  cwd=self.vault_path.parent,
                  timeout=60,
                  check=True
              )
              return True
          except:
              return False

      def _recover_pm2_processes(self) -> bool:
          """Restart PM2 processes."""
          try:
              subprocess.run(["pm2", "restart", "all"], check=True)
              time.sleep(5)
              result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
              processes = json.loads(result.stdout)
              return all(p['pm2_env']['status'] == 'online' for p in processes)
          except:
              return False

      def _recover_disk_space(self) -> bool:
          """Clean up disk space."""
          try:
              # Clean old logs
              subprocess.run(["find", "logs/", "-name", "*.log", "-mtime", "+7", "-delete"])

              # Clean old Done files (older than 30 days)
              subprocess.run(["find", str(self.vault_path / "Done"), "-mtime", "+30", "-delete"])

              # Clean package caches
              subprocess.run(["sudo", "apt", "clean"])

              return True
          except:
              return False
  ```

- [ ] **6.3.2 Integrate Recovery with Health Monitor** (30 min)
  Update `src/core/health_monitor.py`:
  ```python
  from src.core.recovery_handler import RecoveryHandler

  class HealthMonitor:
      def __init__(self, ...):
          # ... existing code ...
          self.recovery_handler = RecoveryHandler(vault_path, agent_mode)

      def monitor_loop(self):
          """Continuous monitoring with auto-recovery."""
          while True:
              status = self.check_health()

              if status.status in ["degraded", "critical"]:
                  print(f"⚠️  Issues detected: {status.issues}")

                  # Attempt recovery
                  recovered = self.recovery_handler.attempt_recovery(status)

                  if recovered:
                      print("✅ Recovery successful")
                      # Re-check health
                      status = self.check_health()
                  else:
                      print("❌ Recovery failed, sending alert")

              time.sleep(300)  # Check every 5 minutes
  ```

- [ ] **6.3.3 Test Auto-Recovery** (30 min)
  ```bash
  # Simulate failures and test recovery

  # Test 1: Vault sync failure
  cd ai_employee_vault
  git remote set-url origin invalid_url
  # Wait for health monitor to detect and recover

  # Test 2: PM2 process crash
  pm2 stop cloud-orchestrator
  # Wait for health monitor to restart

  # Test 3: Disk space (don't actually fill disk!)
  # Mock the check to return high usage
  ```

#### 6.4 Uptime Dashboard (1 hour)

- [ ] **6.4.1 Create Status Page** (45 min)
  Create `scripts/generate_status_page.py`:
  ```python
  """Generate simple status page HTML."""

  def generate_status_page(vault_path: Path):
      """Generate status page from health logs."""
      # Read recent health checks
      # Calculate uptime percentage
      # Show current status
      # Generate HTML

      html = f"""
      <!DOCTYPE html>
      <html>
      <head>
          <title>AI Employee Status</title>
          <meta http-equiv="refresh" content="60">
          <style>
              body {{ font-family: sans-serif; max-width: 800px; margin: 50px auto; }}
              .status {{ padding: 20px; border-radius: 5px; margin: 20px 0; }}
              .healthy {{ background: #d4edda; color: #155724; }}
              .degraded {{ background: #fff3cd; color: #856404; }}
              .critical {{ background: #f8d7da; color: #721c24; }}
          </style>
      </head>
      <body>
          <h1>AI Employee Status</h1>
          <div class="status healthy">
              <h2>✅ System Operational</h2>
              <p>All services running normally</p>
          </div>
          <h3>Services</h3>
          <ul>
              <li>Cloud Agent: ✅ Online</li>
              <li>Vault Sync: ✅ Synced 2 minutes ago</li>
              <li>Odoo: ✅ Reachable</li>
          </ul>
          <h3>Uptime (Last 30 days)</h3>
          <p>99.8%</p>
          <p><small>Last updated: {datetime.now()}</small></p>
      </body>
      </html>
      """

      return html
  ```

- [ ] **6.4.2 Serve Status Page** (15 min)
  ```bash
  # Add to nginx config
  location /status {
      alias /opt/ai-employee/status.html;
  }

  # Schedule generation
  */5 * * * * python scripts/generate_status_page.py > /opt/ai-employee/status.html
  ```

**Checkpoint:** Health monitoring active, alerts working, auto-recovery tested, status visible

---

## Phase 7: Integration Testing & Platinum Demo

**Estimated Time:** 6 hours
**Goal:** End-to-end testing, verify all requirements, prepare platinum demo

### Tasks

#### 7.1 End-to-End Testing (3 hours)

- [ ] **7.1.1 Test Cloud Email Workflow** (45 min)
  Scenario: Email arrives while Local is offline
  1. Stop Local agent
  2. Send test email to monitored inbox
  3. Wait for Cloud to detect (max 2 min)
  4. Verify Cloud triages email
  5. Verify Cloud drafts reply
  6. Verify draft in Pending_Approval/cloud/email_drafts/
  7. Verify git syncs draft
  8. Start Local agent
  9. Local pulls vault
  10. User approves draft: `python scripts/approve.py approve ...`
  11. Verify draft moves to Approved/email_ready/
  12. Verify Local sends email
  13. Verify email in Done/
  14. Verify git syncs completion
  15. Verify Cloud sees completed task

- [ ] **7.1.2 Test Cloud Social Workflow** (45 min)
  Scenario: Cloud generates social post draft
  1. Create content idea in Need_Action/social_posts/
  2. Git sync
  3. Cloud claims task
  4. Cloud generates LinkedIn post draft
  5. Draft saved to Pending_Approval/cloud/social_drafts/
  6. Git sync
  7. Local sees draft
  8. User approves
  9. Local posts to LinkedIn
  10. Moves to Done/

- [ ] **7.1.3 Test Odoo Workflow** (45 min)
  Scenario: Cloud drafts invoice, Local posts
  1. Create invoice request in Need_Action/
  2. Cloud drafts invoice entry
  3. Saves to Pending_Approval/cloud/odoo_drafts/
  4. Local reviews and approves
  5. Local posts to Odoo via MCP
  6. Verify invoice in Odoo
  7. Log in Logs/audit.jsonl

- [ ] **7.1.4 Test Claim-by-Move Conflicts** (45 min)
  Scenario: Both agents try to claim same task
  1. Create task in Need_Action/
  2. Start both agents simultaneously
  3. Verify only one claims task
  4. Verify other agent sees task as claimed
  5. Verify no duplicate processing

#### 7.2 Platinum Demo Preparation (2 hours)

- [ ] **7.2.1 Create Demo Script** (1 hour)
  Create `PLATINUM_DEMO.md`:
  ```markdown
  # Platinum Tier Demo Script

  ## Setup (5 minutes)
  1. Show Cloud VM status: `pm2 status`
  2. Show vault structure: `tree ai_employee_vault/ -L 2`
  3. Show git log: `git log --oneline -5`
  4. Show health status: `python scripts/health_check.py`

  ## Demo: Email Workflow (10 minutes)

  ### Scenario
  Important email arrives while you're away from computer.
  Cloud Agent handles triage and drafts reply.
  When you return, you review and approve.

  ### Steps
  1. **Send test email** (pre-prepared)
     - Subject: "Urgent: Project Deadline Change"
     - Body: "We need to move the deadline to Friday..."

  2. **Show Cloud detecting** (live on Cloud VM)
     ```bash
     ssh ubuntu@<cloud-ip>
     pm2 logs cloud-gmail-watcher --lines 20
     ```
     - Watch as email detected
     - Triage performed
     - Draft generated

  3. **Show vault update** (on Local)
     ```bash
     cd ai_employee_vault
     git pull
     ls Pending_Approval/cloud/email_drafts/
     cat Pending_Approval/cloud/email_drafts/DRAFT_*.md
     ```

  4. **Review and approve** (interactive)
     ```bash
     python scripts/approve.py list
     python scripts/approve.py approve \
       ai_employee_vault/Pending_Approval/cloud/email_drafts/DRAFT_*.md \
       --category email
     ```

  5. **Show Local sending** (live)
     ```bash
     # Local watcher detects approved draft
     # Sends email via Gmail API
     # Moves to Done/
     ```

  6. **Show completion** (both agents)
     - Cloud: `git pull && ls Done/`
     - Local: `ls Done/`
     - Both see completed task

  ## Demo: Always-On Monitoring (5 minutes)

  1. **Show health dashboard**
     - Visit: `https://odoo.yourdomain.com/status`
     - Show uptime: 99.8%
     - Show all services green

  2. **Show PM2 processes**
     ```bash
     pm2 status
     pm2 logs --lines 10
     ```

  3. **Simulate failure and recovery**
     ```bash
     pm2 stop cloud-orchestrator
     # Wait 5 seconds
     pm2 logs cloud-health-monitor
     # Watch auto-recovery restart process
     ```

  ## Demo: Work-Zone Separation (5 minutes)

  1. **Show Cloud restrictions**
     ```bash
     ssh ubuntu@<cloud-ip>
     cat .env.cloud | grep -v "^#"
     # Note: No WhatsApp, no payment credentials
     ```

  2. **Show Local privileges**
     ```bash
     cat .env | grep WHATSAPP
     cat .env | grep PAYMENT
     # Has full access
     ```

  3. **Show audit trail**
     ```bash
     cat ai_employee_vault/Logs/audit.jsonl | tail -10 | jq
     # Shows agent attribution for all actions
     ```

  ## Success Criteria ✅
  - [ ] Email workflow: Cloud drafts → Local approves → Local sends
  - [ ] Always-on: Cloud running 24/7, health monitored
  - [ ] Work-zone separation: Cloud can't send, Local can
  - [ ] Vault sync: Changes visible to both agents
  - [ ] Security: Secrets never synced
  - [ ] Odoo: Accessible, integrated via MCP
  ```

- [ ] **7.2.2 Record Demo Video** (optional) (1 hour)
  - Screen record full workflow
  - Split screen: Cloud terminal + Local terminal
  - Narrate key points
  - Upload to YouTube/internal

#### 7.3 Documentation Finalization (1 hour)

- [ ] **7.3.1 Update README** (30 min)
  Update `README.md`:
  - Add Platinum Tier section
  - Document Cloud + Local architecture
  - Add deployment instructions
  - Add demo instructions

- [ ] **7.3.2 Create Platinum Summary** (30 min)
  Create `PLATINUM_TIER_COMPLETE.md`:
  ```markdown
  # Platinum Tier Implementation Complete ✅

  ## Implemented Features

  ### 1. Cloud Deployment (24/7 Always-On)
  - Oracle Cloud Free VM deployed
  - PM2 process management
  - All watchers + orchestrator running
  - Uptime: 99.8%

  ### 2. Work-Zone Specialization
  - Cloud: Email triage, draft replies, social drafts, Odoo drafts
  - Local: Approvals, WhatsApp, payments, final execution
  - Clear domain boundaries enforced

  ### 3. Vault-Based Delegation
  - Git-based sync (5-minute intervals)
  - Claim-by-move task ownership
  - Conflict-free coordination
  - Single-writer rules enforced

  ### 4. Security
  - Secrets never synced (.gitignore)
  - Cloud: Minimal credentials (read-only Gmail, Odoo)
  - Local: Full credentials (WhatsApp, payments, banking)
  - Audit logging with agent attribution

  ### 5. Odoo Integration
  - Odoo 17 Community deployed on Cloud VM
  - HTTPS enabled (Let's Encrypt)
  - Automated daily backups
  - MCP integration (Cloud read-only, Local read-write)

  ### 6. Health Monitoring
  - Automated health checks (5-minute intervals)
  - Multi-channel alerting (email, webhook)
  - Auto-recovery for common failures
  - Status dashboard

  ## Platinum Demo Passing

  ✅ Email arrives while Local offline
  ✅ Cloud detects and triages
  ✅ Cloud drafts reply
  ✅ Saves to Pending_Approval/
  ✅ Git syncs to Local
  ✅ User approves when returns
  ✅ Local executes send via Gmail API
  ✅ Logs action
  ✅ Moves to Done/
  ✅ Git syncs completion
  ✅ Cloud sees completed task

  ## Cost Breakdown

  | Component | Service | Cost |
  |-----------|---------|------|
  | Cloud VM | Oracle Cloud Free Tier | $0 |
  | AI Reasoning | Groq API Free Tier | $0 |
  | Odoo | Self-hosted | $0 |
  | Vault Sync | Git (GitHub Free) | $0 |
  | **Total** | | **$0/month** |

  ## Next Steps (Optional Phase 2)

  - [ ] Agent-to-Agent messaging (replace some file handoffs)
  - [ ] Advanced workflow orchestration
  - [ ] Multi-region deployment
  - [ ] Load balancing
  - [ ] Kubernetes deployment
  ```

**Checkpoint:** Platinum demo passing, all requirements met, documentation complete

---

## Phase 8 (Optional): Agent-to-Agent Upgrade

**Estimated Time:** 8 hours (Optional)
**Goal:** Replace some file-based communication with direct A2A messages

This phase is optional and can be done after Platinum Tier is complete and stable.

### Tasks

- [ ] **8.1 Design A2A Protocol** (2 hours)
  - Message format (JSON-RPC?)
  - Transport (WebSocket/HTTP/Redis?)
  - Authentication
  - Message types (request, response, event)

- [ ] **8.2 Implement A2A Server** (3 hours)
  - Create message broker
  - Implement pub/sub
  - Add encryption
  - Test latency

- [ ] **8.3 Migrate Select Workflows to A2A** (2 hours)
  - Email draft approval (file → A2A)
  - Health status updates (file → A2A)
  - Keep vault as audit record

- [ ] **8.4 Test A2A vs File-Based** (1 hour)
  - Performance comparison
  - Reliability comparison
  - Decide on hybrid approach

**Note:** Vault remains the source of truth for audit purposes even with A2A.

---

## Testing Checklist

### Unit Tests
- [ ] Task claim handler
- [ ] Approval handler
- [ ] Health monitor
- [ ] Recovery handler
- [ ] Vault sync service

### Integration Tests
- [ ] Cloud → Local email workflow
- [ ] Cloud → Local social workflow
- [ ] Cloud → Local Odoo workflow
- [ ] Claim-by-move race conditions
- [ ] Git conflict resolution
- [ ] Health monitoring and alerts
- [ ] Auto-recovery scenarios

### System Tests
- [ ] 24-hour continuous operation
- [ ] Simulated Cloud VM reboot
- [ ] Simulated network partition
- [ ] Simulated disk full
- [ ] Simulated git conflicts

### Security Tests
- [ ] Secrets never synced (scan git history)
- [ ] Cloud cannot send emails
- [ ] Cloud cannot access WhatsApp
- [ ] Cloud cannot execute payments
- [ ] Audit log complete

### Performance Tests
- [ ] Vault sync latency
- [ ] Task claim latency
- [ ] Email draft-to-send time
- [ ] Health check overhead

---

## Success Criteria

### Minimum Passing Gate (Platinum Demo)

✅ **The following workflow must work flawlessly:**

1. Email arrives while Local agent is offline
2. Cloud agent (running 24/7) detects email within 2 minutes
3. Cloud agent triages email and drafts reply
4. Cloud agent writes draft to `Pending_Approval/cloud/email_drafts/`
5. Git sync propagates draft to Local (within 5 minutes)
6. When Local agent returns online, user sees pending approval
7. User approves draft (via CLI or manual move to `Approved/email_ready/`)
8. Local agent detects approved draft
9. Local agent sends email via Gmail API (MCP)
10. Local agent logs action to `Logs/audit.jsonl`
11. Local agent moves task to `Done/`
12. Git sync propagates completion
13. Cloud agent sees completed task in `Done/`

**All steps must complete successfully with full audit trail.**

### Additional Requirements

- [ ] Cloud VM uptime > 99% over 7 days
- [ ] No secrets leaked to git repository
- [ ] No duplicate task processing
- [ ] All PM2 processes auto-restart on failure
- [ ] Health alerts delivered within 5 minutes of issue
- [ ] Odoo accessible 24/7 over HTTPS
- [ ] Vault sync successful > 99% of attempts

---

## Timeline Estimate

| Phase | Estimated Time | Cumulative |
|-------|----------------|------------|
| Phase 0: Planning | 2 hours | 2h |
| Phase 1: Cloud Infrastructure | 8 hours | 10h |
| Phase 2: Vault Sync & Delegation | 10 hours | 20h |
| Phase 3: Work-Zone Specialization | 12 hours | 32h |
| Phase 4: Cloud Odoo Deployment | 10 hours | 42h |
| Phase 5: Security & Secrets | 6 hours | 48h |
| Phase 6: Health Monitoring | 8 hours | 56h |
| Phase 7: Integration Testing & Demo | 6 hours | 62h |
| **Total (Minimum)** | **62 hours** | |
| Phase 8: A2A Upgrade (Optional) | 8 hours | 70h |
| **Total (with Phase 8)** | **70 hours** | |

---

## Risk Mitigation

### High-Risk Areas

1. **Git Merge Conflicts**
   - Mitigation: Single-writer rules, auto-resolve strategy
   - Fallback: Manual resolution procedure documented

2. **Secrets Leakage**
   - Mitigation: Comprehensive .gitignore, pre-commit hooks
   - Fallback: Rotate all secrets if leak detected

3. **Cloud VM Costs**
   - Mitigation: Use Oracle Cloud Free Tier (always free)
   - Fallback: Budget alerts, automatic shutdown scripts

4. **Task Double-Processing**
   - Mitigation: Claim-by-move atomic operations
   - Fallback: Idempotency checks in execution

5. **Odoo Data Loss**
   - Mitigation: Automated daily backups, off-site storage
   - Fallback: Point-in-time recovery procedure

---

## Maintenance Plan

### Daily
- [ ] Check health dashboard
- [ ] Review audit logs for anomalies
- [ ] Verify git sync working

### Weekly
- [ ] Review alert history
- [ ] Check disk space trends
- [ ] Test backup restoration
- [ ] Update dependencies

### Monthly
- [ ] Security audit
- [ ] Performance review
- [ ] Cost review (should still be $0)
- [ ] Update documentation

---

## Completion Verification

When all phases are complete and all tests pass, verify:

- [ ] Platinum demo executes successfully 3 times in a row
- [ ] System runs unattended for 7 days without issues
- [ ] All documentation is complete and accurate
- [ ] Code is committed and pushed to repository
- [ ] Backups are verified and restorable
- [ ] Handoff document created for future maintenance

**Congratulations! Platinum Tier Complete! 🏆**

---

## Notes

- This is a living document - update as implementation progresses
- Mark tasks complete with dates
- Add notes for any deviations from plan
- Document any additional tasks discovered during implementation
- Track actual time vs estimated time for future planning

**Implementation Start Date:** `_______________`
**Target Completion Date:** `_______________`
**Actual Completion Date:** `_______________`

---

*Generated for hackathon_zero Platinum Tier implementation*
*Last Updated: 2026-01-30*
