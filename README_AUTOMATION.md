# 🤖 GitHub Daily Auto-Commit Automation

Continuous daily GitHub commits for the **voice-agent** repository using **GitHub Actions**.

Once set up, this repository will automatically commit and push activity daily with zero manual intervention required.

---

## 🏗️ Architecture & How It Works

```
GitHub Actions Schedule (cron: '0 11 * * *' / 11:00 UTC daily)
  │
  ├─► Checkout Repository (fetch-depth: 0)
  │
  ├─► Random Delay (0–1800s, scheduled runs only)
  │
  ├─► Execute Python Keepalive Generator (scripts/daily_keepalive.py)
  │     └─ Appends timestamped entry to activity.txt (rolling 365 max)
  │
  ├─► Git Staging & Diff Verification
  │
  ├─► Commit with Randomized Keepalive Message
  │
  └─► Resilient Git Push (Fetch + Rebase + 3x Exponential Backoff Retry)
```

---

## 📁 Key File Overview

| Path | Purpose |
|---|---|
| `.github/workflows/daily_auto_commit.yml` | GitHub Actions workflow definition |
| `scripts/daily_keepalive.py` | Python script to update `activity.txt` atomically |
| `activity.txt` | Timestamped keepalive activity log (rolling max 365 entries) |
| `README_AUTOMATION.md` | Architecture and maintenance guide |

---

## 🔒 Security & Token Permissions

- **Zero Secrets / Keyless**: Uses the standard GitHub Actions automatically generated `GITHUB_TOKEN`.
- **Minimal Scopes**: Configured explicitly with `permissions: contents: write`.
- **Environment Isolation**: `.env` and local secret files are strictly ignored via `.gitignore`. `.env.example` contains placeholders only.

---

## 🚀 Manual Execution & Testing

You can manually trigger a workflow run at any time without waiting for the scheduled cron:

### Via GitHub CLI (`gh`)
```bash
gh workflow run daily_auto_commit.yml
gh run watch
```

### Via GitHub Web UI
1. Navigate to your repository on GitHub: `https://github.com/HammadAli08/voice-agent`
2. Click the **Actions** tab.
3. Select **Daily Auto Commit** from the left sidebar.
4. Click **Run workflow** -> **Run workflow**.

---

## 🛡️ Reliability & Self-Healing Safeguards

- **Rebase & Retry**: Handles remote conflicts or concurrent pushes automatically using `git rebase` and up to 3 push retries.
- **Rolling Log Cap**: Keeps a rolling window of up to 365 entries in `activity.txt` to prevent unbounded repository bloat over years.
- **Conditional Delay**: Random delay (up to 30 minutes) only applies to scheduled runs. Manual dispatch runs immediately for fast feedback.
- **Concurrency Control**: `concurrency: group: daily-auto-commit` prevents overlapping workflow executions.
- **GitHub Inactivity Safeguard Note**: GitHub automatically pauses scheduled workflows on repos with no activity for 60 days. If paused by GitHub, triggering manual dispatch (`gh workflow run`) or making a manual commit immediately re-enables the schedule.

---

*Verified and maintained by GitHub Actions — voice-agent repository*
