#!/bin/bash
# Stop script for filesystem watcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/watcher.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/watcher.pid")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm "$PROJECT_ROOT/watcher.pid"
        echo "Filesystem watcher stopped (PID: $PID)"
    else
        echo "Process with PID $PID not found"
        rm "$PROJECT_ROOT/watcher.pid"
    fi
else
    echo "No PID file found. Is the watcher running?"
fi