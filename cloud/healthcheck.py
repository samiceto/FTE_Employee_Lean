"""
Cloud Health Monitor Sidecar
Runs inside Docker alongside Odoo, writes health status to vault Updates/cloud/
"""
import os
import time
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

VAULT_PATH = os.getenv("VAULT_PATH", "/vault")
ODOO_URL = os.getenv("ODOO_URL", "http://odoo:8069")
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))


def check_odoo() -> dict:
    try:
        req = urllib.request.urlopen(f"{ODOO_URL}/web/health", timeout=10)
        if req.status == 200:
            return {"status": "healthy", "code": 200}
        return {"status": "degraded", "code": req.status}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


def write_health(vault: Path, health: dict):
    updates_dir = vault / "Updates" / "cloud"
    updates_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)

    health_file = updates_dir / "odoo_health.md"
    status_icon = {"healthy": "✅", "degraded": "⚠️", "offline": "❌"}.get(health["status"], "❓")
    health_file.write_text(
        f"---\nagent: cloud_healthcheck\ntimestamp: {ts.isoformat()}\ntype: odoo_health\n---\n\n"
        f"## Odoo Health — {ts.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"| Field | Value |\n|-------|-------|\n"
        f"| Status | {status_icon} {health['status'].upper()} |\n"
        f"| Odoo URL | {ODOO_URL} |\n"
        f"| Checked | {ts.strftime('%Y-%m-%d %H:%M UTC')} |\n"
        + (f"| Error | {health.get('error', '')} |\n" if health.get("error") else "")
    )


def main():
    vault = Path(VAULT_PATH)
    print(f"Health monitor started — checking {ODOO_URL} every {CHECK_INTERVAL}s")
    while True:
        health = check_odoo()
        write_health(vault, health)
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Odoo: {health['status']}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
