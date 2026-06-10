# Filesystem Watcher Service

This service monitors the Inbox folder and moves new files to the Need_Action folder.

## Directory Structure

```
/mnt/d/FTE_Employee/hackathon_zero/
├── src/
│   └── watcher/
│       ├── filesystem_watcher.py          # Original watcher script
│       └── filesystem_watcher_daemon.py   # Enhanced daemon version
├── scripts/
│   ├── start_filesystem_watcher.sh        # Script to start the service
│   ├── stop_filesystem_watcher.sh         # Script to stop the service
│   └── check_filesystem_watcher.sh        # Health check script
├── config/
│   ├── filesystem-watcher.service         # Systemd service file (for traditional Linux)
│   └── filesystem-watcher.conf            # Configuration file
├── logs/
│   └── watcher.log                        # Log file for the service
├── watcher.pid                            # Process ID file
└── SERVICE_SETUP_README.md                # This documentation
```

## Files Created

- `src/watcher/filesystem_watcher_daemon.py` - Enhanced version of the original watcher with better error handling
- `scripts/start_filesystem_watcher.sh` - Script to start the service
- `scripts/stop_filesystem_watcher.sh` - Script to stop the service
- `scripts/check_filesystem_watcher.sh` - Health check script
- `config/filesystem-watcher.service` - Systemd service file (for traditional Linux)
- `config/filesystem-watcher.conf` - Configuration file
- `logs/watcher.log` - Log file for the service
- `watcher.pid` - Process ID file (in project root)

## Running the Service

### Manual Start/Stop

```bash
# Start the service
./scripts/start_filesystem_watcher.sh

# Stop the service
./scripts/stop_filesystem_watcher.sh

# Check service status
./scripts/check_filesystem_watcher.sh
```

### Automatic Start on Boot

#### For Traditional Linux Systems (with systemd):

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp config/filesystem-watcher.service /etc/systemd/system/
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start at boot:
   ```bash
   sudo systemctl enable filesystem-watcher.service
   ```

4. Start the service:
   ```bash
   sudo systemctl start filesystem-watcher.service
   ```

#### For WSL (Windows Subsystem for Linux):

Since WSL doesn't run systemd by default, use one of these approaches:

**Option 1: Using Windows Task Scheduler**
1. Create a Windows batch file that starts your WSL service
2. Schedule it to run when Windows starts

**Option 2: Add to WSL startup script**
Add the start command to your shell profile:
```bash
echo "/mnt/d/FTE_Employee/hackathon_zero/scripts/start_filesystem_watcher.sh" >> ~/.bashrc
```

**Option 3: Using WSL's /etc/rc.local (if configured)**
If you have rc.local configured in WSL:
```bash
echo "/mnt/d/FTE_Employee/hackathon_zero/scripts/start_filesystem_watcher.sh" | sudo tee -a /etc/rc.local
```

## Checking Service Status

Monitor the log file:
```bash
tail -f logs/watcher.log
```

Check if the process is running:
```bash
ps aux | grep filesystem_watcher_daemon.py
```

## Dependencies

The service requires the `watchdog` Python package:
```bash
pip install --break-system-packages watchdog
```

## Troubleshooting

- Check `logs/watcher.log` for error messages
- Verify that the ai_employee_vault/Inbox and ai_employee_vault/Need_Action directories exist
- Ensure the script has execute permissions
- Confirm the Python interpreter can be found at `/usr/bin/python3`