#!/bin/bash
# Start the Claude Reasoning Loop Orchestrator
# This script runs the reasoning agent that analyzes tasks and creates Plan.md files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Default values
VAULT_PATH="${VAULT_PATH:-$PROJECT_ROOT/ai_employee_vault}"
INTERVAL="${INTERVAL:-1800}"  # 30 minutes
MIN_TASKS="${MIN_TASKS:-1}"
COOLDOWN="${COOLDOWN:-60}"  # 60 minutes

echo "🧠 Starting Claude Reasoning Loop"
echo "   Vault: $VAULT_PATH"
echo "   Interval: ${INTERVAL}s"
echo "   Min Tasks: $MIN_TASKS"
echo "   Cooldown: ${COOLDOWN}m"
echo ""

# Run the orchestrator
cd "$PROJECT_ROOT"
python -m src.orchestrator.reasoning_loop \
    --vault "$VAULT_PATH" \
    --interval "$INTERVAL" \
    --min-tasks "$MIN_TASKS" \
    --cooldown "$COOLDOWN" \
    "$@"
