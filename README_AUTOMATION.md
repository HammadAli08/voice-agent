# 🤖 GitHub Daily Auto-Commit Automation

Continuous daily GitHub commits for the **voice-agent** repository using **GitHub Actions**.

Once set up, this repository will automatically commit and push activity daily with zero manual intervention required.

---

## 🏗️ Architecture & How It Works

```
GitHub Actions Schedule (cron: '0 11 * * *' / 11:00 UTC daily)
  │
  ├─► Timeout Protection (timeout-minutes: 15)
  │
  ├─► Checkout Repository (fetch-depth: 0)
  │
  ├─► Random Delay (0–600s / 0–10 min, scheduled runs only)
  │
  ├─► Execute Python Keepalive Generator (scripts/daily_keepalive.py)
  │     └─ Appends timestamped entry to activity.txt (rolling 365 max)
  │
  ├─► Git Staging & Diff Verification
  │
  ├─► Commit with Randomized Keepalive Message
  │
  ├─► Resilient Git Push (Fetch + Rebase + 3x Exponential Backoff Retry)
  │
  └─► Strict Remote Verification (Confirms LOCAL HEAD == REMOTE origin/main)
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
- **Strict Remote Verification**: Asserts that `git rev-parse HEAD` on the runner strictly equals `git rev-parse origin/main` after pushing before reporting success.
- **Timeout Protection**: `timeout-minutes: 15` ensures stuck network connections or runner hangs terminate cleanly.
- **Rolling Log Cap**: Keeps a rolling window of up to 365 entries in `activity.txt` to prevent unbounded repository bloat.
- **Conditional Delay**: Random delay (up to 10 minutes) only applies to scheduled runs. Manual dispatch runs immediately for fast feedback.
- **Concurrency Protection**: `concurrency: group: daily-auto-commit` prevents overlapping workflow executions.

---

## ⚠️ Platform Limitation Notice & Maintenance

Scheduled workflows on GitHub Actions are subject to GitHub infrastructure policies:
1. **GitHub Inactivity Policy**: Scheduled workflows pause automatically if a repository has no human or PAT activity for 60 consecutive days. If paused, GitHub sends an email notification; triggering `gh workflow run` or pushing a commit manually reactivates the schedule.
2. **Infrastructure Outages**: Platform-wide GitHub Actions service disruptions or upstream git service downtime will delay workflow execution until services resume.

---

*Verified and maintained by GitHub Actions — voice-agent repository*
