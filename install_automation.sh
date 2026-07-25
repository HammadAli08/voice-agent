#!/usr/bin/env bash
# =============================================================================
# install_automation.sh — One-time setup script for the GitHub commit automation
#
# Run this once:  bash install_automation.sh
# It is fully idempotent — safe to run multiple times.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
SETUP_LOG="${LOG_DIR}/install_automation.log"
SSH_KEY="${HOME}/.ssh/id_ed25519"
REMOTE_URL="git@github.com:HammadAli08/voice-agent.git"

mkdir -p "${LOG_DIR}"

# ── Helpers ───────────────────────────────────────────────────────────────────
OK="✓"
FAIL="✗"
WARN="⚠"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${SETUP_LOG}"; }
pass() { echo "  ${OK} $*" | tee -a "${SETUP_LOG}"; }
fail() { echo "  ${FAIL} $*" | tee -a "${SETUP_LOG}"; }
warn() { echo "  ${WARN} $*" | tee -a "${SETUP_LOG}"; }

log "=========================================="
log "install_automation.sh — starting"
log "Repo: ${SCRIPT_DIR}"

# ── 1. Check Required Tools ───────────────────────────────────────────────────
log "Checking required tools..."

for tool in git python3 ssh-agent ssh-add crontab; do
    if command -v "${tool}" &>/dev/null; then
        pass "${tool} found: $(command -v "${tool}")"
    else
        fail "${tool} not found — attempting install..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y openssh-client git python3 2>>"${SETUP_LOG}"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y openssh-clients git python3 2>>"${SETUP_LOG}"
        elif command -v yum &>/dev/null; then
            sudo yum install -y openssh-clients git python3 2>>"${SETUP_LOG}"
        else
            fail "Cannot auto-install ${tool}. Please install it manually."
            exit 1
        fi
    fi
done

# ── 2. Verify Git Repository ──────────────────────────────────────────────────
log "Verifying Git repository..."

if [[ -d "${SCRIPT_DIR}/.git" ]]; then
    pass "Git repository initialised"
else
    fail "Not a git repo — initialising..."
    git -C "${SCRIPT_DIR}" init
    git -C "${SCRIPT_DIR}" checkout -b main 2>/dev/null || true
    pass "Git repository initialised"
fi

# ── 3. Verify / Fix Remote ────────────────────────────────────────────────────
log "Checking git remote..."

CURRENT_REMOTE=$(git -C "${SCRIPT_DIR}" remote get-url origin 2>/dev/null || echo "")
if [[ -z "${CURRENT_REMOTE}" ]]; then
    fail "No remote 'origin' — adding: ${REMOTE_URL}"
    git -C "${SCRIPT_DIR}" remote add origin "${REMOTE_URL}"
    pass "Remote 'origin' added: ${REMOTE_URL}"
elif [[ "${CURRENT_REMOTE}" == https://* ]]; then
    warn "Remote uses HTTPS — switching to SSH..."
    git -C "${SCRIPT_DIR}" remote set-url origin "${REMOTE_URL}"
    pass "Remote updated to SSH: ${REMOTE_URL}"
else
    pass "Remote origin: ${CURRENT_REMOTE}"
fi

# ── 4. SSH Agent & Key ────────────────────────────────────────────────────────
log "Setting up SSH agent..."

if [[ ! -f "${SSH_KEY}" ]]; then
    fail "SSH key not found: ${SSH_KEY}"
    fail "Generate one with: ssh-keygen -t ed25519 -C 'your@email.com'"
    exit 1
fi

# Source saved agent env if it exists
AGENT_ENV="${HOME}/.ssh/agent-env"
if [[ -f "${AGENT_ENV}" ]]; then
    # shellcheck source=/dev/null
    source "${AGENT_ENV}" > /dev/null 2>&1 || true
fi

if ! ssh-add -l > /dev/null 2>&1; then
    eval "$(ssh-agent -s)" >> "${SETUP_LOG}" 2>&1
    {
        echo "export SSH_AUTH_SOCK=${SSH_AUTH_SOCK}"
        echo "export SSH_AGENT_PID=${SSH_AGENT_PID}"
    } > "${AGENT_ENV}"
    chmod 600 "${AGENT_ENV}"
    pass "ssh-agent started (PID: ${SSH_AGENT_PID})"
else
    pass "ssh-agent already running"
fi

if ssh-add -l 2>/dev/null | grep -q "ED25519\|RSA\|ECDSA"; then
    pass "SSH key already loaded in agent"
else
    ssh-add "${SSH_KEY}" >> "${SETUP_LOG}" 2>&1 && pass "SSH key loaded" || warn "ssh-add returned non-zero (passphrase key?)"
fi

# ── 5. Test SSH Authentication ────────────────────────────────────────────────
log "Testing SSH authentication to GitHub..."
SSH_TEST=$(ssh -o BatchMode=yes -o ConnectTimeout=10 -T git@github.com 2>&1 || true)
if echo "${SSH_TEST}" | grep -q "successfully authenticated"; then
    pass "SSH authentication: OK (${SSH_TEST})"
    SSH_OK=true
else
    warn "SSH test: ${SSH_TEST}"
    SSH_OK=false
fi

# ── 6. Push / Set Upstream ────────────────────────────────────────────────────
log "Setting upstream branch..."

UPSTREAM=$(git -C "${SCRIPT_DIR}" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
if [[ -z "${UPSTREAM}" ]]; then
    warn "Upstream not set — attempting: git push -u origin main"
    if git -C "${SCRIPT_DIR}" push -u origin main >> "${SETUP_LOG}" 2>&1; then
        pass "Upstream set to origin/main"
    else
        warn "Could not push to set upstream (repo may not exist on GitHub yet)."
        warn "Create the repo on GitHub first, then re-run this script."
    fi
else
    pass "Upstream branch: ${UPSTREAM}"
fi

# ── 7. Make Scripts Executable ────────────────────────────────────────────────
log "Setting file permissions..."
chmod +x "${SCRIPT_DIR}/auto_commit.py"
chmod +x "${SCRIPT_DIR}/run_auto_commit.sh"
chmod +x "${SCRIPT_DIR}/setup_cron.py"
chmod +x "${SCRIPT_DIR}/install_automation.sh"
pass "Scripts are executable"

# ── 8. Create logs/ directory ─────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"
pass "logs/ directory ready: ${LOG_DIR}"

# ── 9. Install Cron Job ───────────────────────────────────────────────────────
log "Installing cron job..."
python3 "${SCRIPT_DIR}/setup_cron.py" 2>>"${SETUP_LOG}"
CRON_ENTRY=$(crontab -l 2>/dev/null | grep "auto_commit_job" || echo "")
if [[ -n "${CRON_ENTRY}" ]]; then
    pass "Cron job installed: ${CRON_ENTRY}"
    CRON_OK=true
else
    fail "Cron job installation failed."
    CRON_OK=false
fi

# ── 10. End-to-End Test ───────────────────────────────────────────────────────
log "Running end-to-end test..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Running auto_commit.py (first run test)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 "${SCRIPT_DIR}/auto_commit.py"; then
    TEST_OK=true
    pass "End-to-end test: PASSED"
else
    TEST_OK=false
    fail "End-to-end test: FAILED (see logs/auto_commit.log)"
fi

# Latest commit
LATEST_HASH=$(git -C "${SCRIPT_DIR}" log --oneline -1 2>/dev/null || echo "unknown")

# ── 11. Final Status Report ───────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "           FINAL STATUS REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[[ "${SSH_OK}" == "true" ]]  && echo "  ✓ SSH authentication"  || echo "  ✗ SSH authentication"
REMOTE_NOW=$(git -C "${SCRIPT_DIR}" remote get-url origin 2>/dev/null || echo "")
[[ -n "${REMOTE_NOW}" ]]    && echo "  ✓ Git remote: ${REMOTE_NOW}" || echo "  ✗ Git remote"
UP=$(git -C "${SCRIPT_DIR}" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")
[[ -n "${UP}" ]]            && echo "  ✓ Upstream branch: ${UP}"   || echo "  ⚠ Upstream branch not set (push once to fix)"
[[ -f "${SCRIPT_DIR}/auto_commit.py" ]]   && echo "  ✓ Automation script: auto_commit.py"
[[ "${CRON_OK}" == "true" ]] && echo "  ✓ Cron job installed" || echo "  ✗ Cron job"
[[ "${TEST_OK}" == "true" ]] && echo "  ✓ Test commit"        || echo "  ✗ Test commit"
[[ "${SSH_OK}" == "true" && "${TEST_OK}" == "true" ]] && echo "  ✓ GitHub push" || echo "  ⚠ GitHub push (verify manually)"
echo "  ✓ Log file: ${LOG_DIR}/auto_commit.log"
echo ""
echo "  Latest commit: ${LATEST_HASH}"
echo ""
echo "  Installed cron:"
crontab -l 2>/dev/null | grep "auto_commit" || echo "  (none)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete! Full log: ${SETUP_LOG}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
