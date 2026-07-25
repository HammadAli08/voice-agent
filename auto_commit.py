#!/usr/bin/env python3
"""
auto_commit.py - Daily GitHub commit automation for voice-agent repository.

Creates/updates activity.txt, commits, and pushes to GitHub automatically.
Logs all activity to logs/auto_commit.log.
"""

import os
import sys
import random
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
REPO_DIR = Path(__file__).parent.resolve()
ACTIVITY_FILE = REPO_DIR / "activity.txt"
LOG_DIR = REPO_DIR / "logs"
LOG_FILE = LOG_DIR / "auto_commit.log"

KEEPALIVE_MESSAGES = [
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
]

COMMIT_MESSAGES = [
    "chore: daily automated maintenance",
    "chore: repository health check",
    "chore: scheduled metadata refresh",
    "chore: automated keepalive update",
    "chore: routine repository sync",
    "chore: periodic activity log",
    "chore: daily workflow update",
    "chore: automated housekeeping",
    "chore: scheduled system check",
    "chore: routine maintenance update",
]

# ── Logging Setup ──────────────────────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    """Configure file and console logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("auto_commit")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    # File handler — full debug detail
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ── Helpers ────────────────────────────────────────────────────────────────────
def run(cmd: list[str], logger: logging.Logger, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command, log it, and return the result."""
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=str(REPO_DIR),
        capture_output=capture,
        text=True,
    )
    if result.stdout:
        logger.debug("stdout: %s", result.stdout.strip())
    if result.stderr:
        logger.debug("stderr: %s", result.stderr.strip())
    return result


def ensure_ssh_agent(logger: logging.Logger) -> None:
    """Verify SSH agent has keys loaded; warn if not."""
    result = subprocess.run(["ssh-add", "-l"], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("SSH agent active with %d key(s).", result.stdout.count("\n"))
    else:
        logger.warning(
            "SSH agent has no keys loaded. Push may fail if key is passphrase-protected. "
            "Run: ssh-add ~/.ssh/id_ed25519"
        )


def verify_git_config(logger: logging.Logger) -> bool:
    """Check that git, remote, and upstream branch are properly configured."""
    ok = True

    # Check git is initialised
    if not (REPO_DIR / ".git").exists():
        logger.error("Not a git repository: %s", REPO_DIR)
        return False

    # Check origin remote
    result = run(["git", "remote", "get-url", "origin"], logger)
    if result.returncode != 0:
        logger.error("Git remote 'origin' not set.")
        return False

    remote_url = result.stdout.strip()
    logger.info("Remote origin: %s", remote_url)

    if remote_url.startswith("https://"):
        logger.warning(
            "Remote uses HTTPS — SSH recommended. "
            "Fix with: git remote set-url origin git@github.com:USER/REPO.git"
        )

    # Check upstream is set
    result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], logger)
    if result.returncode != 0:
        logger.warning("No upstream branch set. Attempting to set origin/main…")
        set_result = run(["git", "push", "--set-upstream", "origin", "main"], logger)
        if set_result.returncode != 0:
            logger.error("Failed to set upstream: %s", set_result.stderr.strip())
            ok = False
        else:
            logger.info("Upstream branch set to origin/main.")
    else:
        logger.info("Upstream branch: %s", result.stdout.strip())

    return ok


def update_activity_file(logger: logging.Logger) -> None:
    """Append a timestamped keepalive entry to activity.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = random.choice(KEEPALIVE_MESSAGES)
    entry = f"[{timestamp}] {message}\n"

    ACTIVITY_FILE.touch(exist_ok=True)
    with open(ACTIVITY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    logger.info("activity.txt updated: %s", entry.strip())


def has_changes(logger: logging.Logger) -> bool:
    """Return True if there are staged or unstaged changes."""
    result = run(["git", "status", "--porcelain"], logger)
    changed = bool(result.stdout.strip())
    if changed:
        logger.info("Changes detected:\n%s", result.stdout.strip())
    else:
        logger.info("No changes detected — skipping commit.")
    return changed


def git_add(logger: logging.Logger) -> bool:
    result = run(["git", "add", "."], logger)
    if result.returncode != 0:
        logger.error("git add failed: %s", result.stderr.strip())
        return False
    logger.info("git add . — OK")
    return True


def git_commit(logger: logging.Logger) -> bool:
    message = random.choice(COMMIT_MESSAGES)
    result = run(["git", "commit", "-m", message], logger)
    if result.returncode != 0:
        # Likely nothing to commit (edge case)
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            logger.info("Nothing new to commit (already clean after add).")
            return False
        logger.error("git commit failed: %s", result.stderr.strip())
        return False
    logger.info("Committed: %s", message)
    return True


def git_push(logger: logging.Logger) -> bool:
    result = run(["git", "push"], logger)
    if result.returncode != 0:
        logger.error("git push failed: %s", result.stderr.strip())
        return False
    logger.info("Pushed to remote successfully.")
    return True


def show_latest_commit(logger: logging.Logger) -> None:
    result = run(["git", "log", "--oneline", "-1"], logger)
    if result.returncode == 0:
        logger.info("Latest commit: %s", result.stdout.strip())


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> int:
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("auto_commit.py started — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("Repository: %s", REPO_DIR)

    try:
        ensure_ssh_agent(logger)

        if not verify_git_config(logger):
            logger.error("Git configuration check failed. Aborting.")
            return 1

        # Always update the activity file (creates if missing)
        update_activity_file(logger)

        if not has_changes(logger):
            logger.info("Nothing to commit. Exiting cleanly.")
            show_latest_commit(logger)
            return 0

        if not git_add(logger):
            return 1

        committed = git_commit(logger)
        if not committed:
            logger.info("Commit skipped.")
            return 0

        if not git_push(logger):
            return 1

        show_latest_commit(logger)
        logger.info("auto_commit.py completed successfully.")
        return 0

    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        return 130
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
