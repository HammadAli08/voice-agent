#!/usr/bin/env python3
"""
Daily Keepalive Entry Generator
Appends timestamped entry to activity.txt with rolling limit safeguard.
"""

import os
import random
from datetime import datetime, timezone

MESSAGES = [
    "Daily maintenance",
    "Repository health check",
    "Metadata refresh",
    "Automated update",
    "Keepalive entry",
    "Routine housekeeping",
    "Scheduled synchronization",
    "Periodic status update",
    "System heartbeat",
    "Automated maintenance run",
    "Repository sync complete",
    "Daily activity log",
    "Workflow continuity check",
    "Routine integrity verification",
    "Scheduled upkeep",
    "Automated pulse check",
    "Continuous integration check",
    "Scheduled environment refresh",
    "System state check",
    "Daily repository validation"
]

MAX_ENTRIES = 365
ACTIVITY_FILE = "activity.txt"

def update_activity_log() -> str:
    msg = random.choice(MESSAGES)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    new_entry = f"[{timestamp}] {msg}\n"

    lines = []
    if os.path.exists(ACTIVITY_FILE):
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    lines.append(new_entry)

    # Maintain rolling max entries
    if len(lines) > MAX_ENTRIES:
        lines = lines[-MAX_ENTRIES:]

    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Successfully updated {ACTIVITY_FILE}: {new_entry.strip()}")
    return msg

if __name__ == "__main__":
    update_activity_log()
