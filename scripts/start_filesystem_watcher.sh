#!/bin/bash
# Startup script for filesystem watcher

# Directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WATCHER_DIR="$PROJECT_ROOT/src/watcher"
LOG_DIR="$PROJECT_ROOT/logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Start the filesystem watcher in the background
nohup python3 "$WATCHER_DIR/filesystem_watcher_daemon.py" > "$LOG_DIR/watcher.log" 2>&1 &

# Save the PID for potential management
echo $! > "$PROJECT_ROOT/watcher.pid"

echo "Filesystem watcher started with PID $(cat $PROJECT_ROOT/watcher.pid)"