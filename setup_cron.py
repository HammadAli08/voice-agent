#!/usr/bin/env python3
"""
setup_cron.py — Installs / rotates the daily auto-commit systemd user timer.

Uses systemd --user timers (no root required). Falls back to crontab if
crontab is available.

Rules:
  • Picks a random time between 09:00 and 19:00 each time it runs.
  • Idempotent — safe to run multiple times.
  • The timer re-runs setup_cron.py on the 1st of each month to rotate time.
"""

import os
import random
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent.resolve()
LAUNCHER = REPO_DIR / "run_auto_commit.sh"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"

SERVICE_NAME = "auto-commit"
TIMER_NAME = "auto-commit"
ROTATE_SERVICE_NAME = "auto-commit-rotate"
ROTATE_TIMER_NAME = "auto-commit-rotate"

# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def random_time() -> tuple[int, int]:
    """Return (hour, minute) randomly between 09:00 and 19:00."""
    hour = random.randint(9, 18)
    minute = random.randint(0, 59)
    return hour, minute


# ── Systemd User Timer ────────────────────────────────────────────────────────
def write_service_file(path: Path, description: str, exec_cmd: str) -> None:
    content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=oneshot
ExecStart={exec_cmd}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""
    path.write_text(content)
    print(f"  Written: {path}")


def write_timer_file(path: Path, description: str, on_calendar: str) -> None:
    content = f"""[Unit]
Description={description}

[Timer]
OnCalendar={on_calendar}
Persistent=true
RandomizedDelaySec=0

[Install]
WantedBy=timers.target
"""
    path.write_text(content)
    print(f"  Written: {path}")


def install_systemd_timer(hour: int, minute: int) -> None:
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)

    # ── Daily commit service ──────────────────────────────────────────────
    write_service_file(
        SYSTEMD_USER_DIR / f"{SERVICE_NAME}.service",
        description="Daily GitHub auto-commit",
        exec_cmd=f"/bin/bash {LAUNCHER}",
    )

    # Daily timer at random time
    on_calendar = f"*-*-* {hour:02d}:{minute:02d}:00"
    write_timer_file(
        SYSTEMD_USER_DIR / f"{TIMER_NAME}.timer",
        description=f"Daily GitHub commit timer ({hour:02d}:{minute:02d})",
        on_calendar=on_calendar,
    )

    # ── Monthly rotation service ──────────────────────────────────────────
    write_service_file(
        SYSTEMD_USER_DIR / f"{ROTATE_SERVICE_NAME}.service",
        description="Monthly auto-commit schedule rotation",
        exec_cmd=f"/usr/bin/python3 {REPO_DIR}/setup_cron.py",
    )

    # Rotate on 1st of each month at 08:00
    write_timer_file(
        SYSTEMD_USER_DIR / f"{ROTATE_TIMER_NAME}.timer",
        description="Monthly rotation of auto-commit schedule",
        on_calendar="*-*-01 08:00:00",
    )

    # ── Reload and enable ─────────────────────────────────────────────────
    run(["systemctl", "--user", "daemon-reload"])

    for unit in [
        f"{TIMER_NAME}.timer",
        f"{ROTATE_TIMER_NAME}.timer",
    ]:
        run(["systemctl", "--user", "enable", "--now", unit])
        print(f"  Enabled: {unit}")

    # ── Enable linger so timers survive logout/reboot ──────────────────────
    username = os.environ.get("USER", os.environ.get("LOGNAME", ""))
    if username:
        result = run(["loginctl", "enable-linger", username], check=False)
        if result.returncode == 0:
            print(f"  Linger enabled for user '{username}' (survives reboot)")
        else:
            print(f"  Warning: loginctl enable-linger failed (may need sudo): {result.stderr.strip()}")

    print(f"\n[OK] Systemd timer installed: daily at {hour:02d}:{minute:02d}")
    print(f"[OK] Monthly rotation timer installed (1st of month at 08:00)")

    # Show timer status
    result = run(["systemctl", "--user", "list-timers", "--no-pager"], check=False)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "auto-commit" in line or "NEXT" in line or "LAST" in line:
                print(f"  {line}")


# ── Crontab Fallback ─────────────────────────────────────────────────────────
CRON_MARKER = "# auto_commit_job"

def get_crontab() -> list[str]:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def set_crontab(lines: list[str]) -> None:
    content = "\n".join(lines) + "\n"
    proc = subprocess.run(["crontab", "-"], input=content, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[ERROR] crontab install failed: {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def install_crontab(hour: int, minute: int) -> None:
    lines = get_crontab()
    # Remove old entries
    lines = [ln for ln in lines if CRON_MARKER not in ln and "auto_commit_rotate" not in ln]

    daily = (
        f"{minute} {hour} * * * "
        f"bash {LAUNCHER} "
        f">> {REPO_DIR}/logs/cron_run.log 2>&1 "
        f"{CRON_MARKER}"
    )
    rotate = (
        f"0 8 1 * * "
        f"python3 {REPO_DIR}/setup_cron.py "
        f">> {REPO_DIR}/logs/cron_rotate.log 2>&1 "
        f"# auto_commit_rotate"
    )

    lines = [ln for ln in lines if ln.strip()]
    lines.extend([daily, rotate])
    set_crontab(lines)
    print(f"[OK] Crontab installed: {minute:02d} {hour:02d} * * * (runs at {hour:02d}:{minute:02d})")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    hour, minute = random_time()

    # Try systemd first (preferred, no root needed)
    systemd_ok = run(["systemctl", "--user", "status"], check=False).returncode in (0, 1)

    if systemd_ok:
        print("[INFO] Using systemd --user timers")
        install_systemd_timer(hour, minute)
        return

    # Fall back to crontab
    crontab_path = subprocess.run(["which", "crontab"], capture_output=True, text=True)
    if crontab_path.returncode == 0:
        print("[INFO] Falling back to crontab")
        install_crontab(hour, minute)
        return

    print("[ERROR] Neither systemd --user nor crontab is available.", file=sys.stderr)
    print("        Install cronie with: sudo dnf install -y cronie && sudo systemctl enable --now crond")
    sys.exit(1)


if __name__ == "__main__":
    main()
