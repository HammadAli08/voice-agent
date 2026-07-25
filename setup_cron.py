#!/usr/bin/env python3
"""
setup_cron.py — Installs / rotates the daily auto-commit cron job.

Rules:
  • Picks a random time between 09:00 and 19:00 each time it runs.
  • Removes any existing auto_commit cron entry before inserting the new one
    (idempotent — never creates duplicates).
  • Called once during initial setup, and once per month by a secondary cron
    entry that rotates the schedule.
"""

import random
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent.resolve()
LAUNCHER = REPO_DIR / "run_auto_commit.sh"
MARKER = "# auto_commit_job"


def get_crontab() -> list[str]:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return []  # No crontab yet
    return result.stdout.splitlines()


def set_crontab(lines: list[str]) -> None:
    content = "\n".join(lines) + "\n"
    proc = subprocess.run(["crontab", "-"], input=content, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[ERROR] crontab install failed: {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def remove_auto_commit_entries(lines: list[str]) -> list[str]:
    """Strip all lines tagged with our marker."""
    return [ln for ln in lines if MARKER not in ln]


def random_time() -> tuple[int, int]:
    """Return (hour, minute) randomly between 09:00 and 19:00."""
    hour = random.randint(9, 18)
    minute = random.randint(0, 59)
    # Ensure we don't exceed 19:00
    if hour == 18:
        minute = random.randint(0, 59)
    return hour, minute


def build_daily_entry(hour: int, minute: int) -> str:
    return (
        f"{minute} {hour} * * * "
        f"bash {LAUNCHER} "
        f">> {REPO_DIR}/logs/cron_run.log 2>&1 "
        f"{MARKER}"
    )


def build_monthly_rotation_entry() -> str:
    """
    On the 1st of every month at 08:00, re-run setup_cron.py
    so the daily time changes automatically.
    """
    return (
        f"0 8 1 * * "
        f"python3 {REPO_DIR}/setup_cron.py "
        f">> {REPO_DIR}/logs/cron_rotate.log 2>&1 "
        f"# auto_commit_rotate"
    )


def main() -> None:
    lines = get_crontab()
    lines = remove_auto_commit_entries(lines)

    # Also remove old rotation entries so we stay idempotent
    lines = [ln for ln in lines if "auto_commit_rotate" not in ln]

    hour, minute = random_time()
    daily_entry = build_daily_entry(hour, minute)
    rotate_entry = build_monthly_rotation_entry()

    lines.append(daily_entry)
    lines.append(rotate_entry)

    # Remove empty trailing lines then set
    lines = [ln for ln in lines if ln.strip()]
    set_crontab(lines)

    print(f"[OK] Daily cron installed: {minute:02d} {hour:02d} * * * (runs at {hour:02d}:{minute:02d})")
    print(f"[OK] Monthly rotation cron installed.")
    print(f"[OK] Launcher: {LAUNCHER}")


if __name__ == "__main__":
    main()
