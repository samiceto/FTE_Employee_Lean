#!/bin/bash
# Health check script for filesystem watcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

if [ -f "$PROJECT_ROOT/watcher.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/watcher.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Filesystem watcher is running (PID: $PID)"
        echo "Last log entry:"
        tail -n 1 "$LOG_DIR/watcher.log"
        exit 0
    else
        echo "Process with PID $PID not found. Service may have crashed."
        exit 1
    fi
else
    echo "PID file not found. Service may not be running."
    exit 1
fi