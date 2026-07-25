#!/usr/bin/env bash
# =============================================================================
# run_auto_commit.sh — Launcher for auto_commit.py
#
# Responsibilities:
#   1. Start ssh-agent if not already running
#   2. Load the SSH private key (passphrase-free assumed for automation)
#   3. Execute auto_commit.py
#   4. Write timestamped execution logs to logs/run_auto_commit.log
# =============================================================================

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
RUN_LOG="${LOG_DIR}/run_auto_commit.log"
SSH_KEY="${HOME}/.ssh/id_ed25519"
PYTHON_SCRIPT="${SCRIPT_DIR}/auto_commit.py"

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"

log() {
    local level="$1"; shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*" | tee -a "${RUN_LOG}"
}

log "INFO" "=========================================="
log "INFO" "run_auto_commit.sh started"
log "INFO" "Working directory: ${SCRIPT_DIR}"

# ── SSH Agent Setup ───────────────────────────────────────────────────────────
start_ssh_agent() {
    log "INFO" "Starting new ssh-agent..."
    eval "$(ssh-agent -s)" >> "${RUN_LOG}" 2>&1
    # Persist socket path for this session
    export SSH_AUTH_SOCK SSH_AGENT_PID
    log "INFO" "ssh-agent started (PID: ${SSH_AGENT_PID})"
}

load_ssh_key() {
    if [[ ! -f "${SSH_KEY}" ]]; then
        log "ERROR" "SSH key not found: ${SSH_KEY}"
        exit 1
    fi

    # Check if key is already loaded
    if ssh-add -l 2>/dev/null | grep -q "$(ssh-keygen -lf "${SSH_KEY}" 2>/dev/null | awk '{print $2}')"; then
        log "INFO" "SSH key already loaded in agent."
        return 0
    fi

    log "INFO" "Loading SSH key: ${SSH_KEY}"
    # Use -q for quiet (no output on success)
    if ssh-add "${SSH_KEY}" >> "${RUN_LOG}" 2>&1; then
        log "INFO" "SSH key loaded successfully."
    else
        log "WARNING" "ssh-add returned non-zero. Key may require a passphrase or agent issue."
    fi
}

# Determine if ssh-agent is functional
if [[ -z "${SSH_AUTH_SOCK:-}" ]] || ! ssh-add -l > /dev/null 2>&1; then
    # Check if there's a running agent socket we can reuse
    AGENT_SOCKET_FILE="${HOME}/.ssh/agent-env"

    if [[ -f "${AGENT_SOCKET_FILE}" ]]; then
        # shellcheck source=/dev/null
        source "${AGENT_SOCKET_FILE}" > /dev/null 2>&1 || true
    fi

    # Re-test after sourcing saved env
    if ! ssh-add -l > /dev/null 2>&1; then
        start_ssh_agent
        # Persist agent environment so future shells can reuse it
        {
            echo "export SSH_AUTH_SOCK=${SSH_AUTH_SOCK}"
            echo "export SSH_AGENT_PID=${SSH_AGENT_PID}"
        } > "${AGENT_SOCKET_FILE}"
        chmod 600 "${AGENT_SOCKET_FILE}"
    else
        log "INFO" "Reusing existing ssh-agent (socket: ${SSH_AUTH_SOCK})"
    fi
else
    log "INFO" "ssh-agent already running (socket: ${SSH_AUTH_SOCK})"
fi

# Load the SSH key
load_ssh_key

# Verify SSH connectivity
log "INFO" "Testing SSH connectivity to GitHub..."
if ssh -o BatchMode=yes -o ConnectTimeout=10 -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    log "INFO" "SSH authentication to GitHub: OK"
else
    log "WARNING" "SSH authentication test inconclusive — proceeding anyway."
fi

# ── Execute Python Script ─────────────────────────────────────────────────────
log "INFO" "Executing: python3 ${PYTHON_SCRIPT}"

if python3 "${PYTHON_SCRIPT}" >> "${RUN_LOG}" 2>&1; then
    EXIT_CODE=0
    log "INFO" "auto_commit.py completed successfully (exit 0)"
else
    EXIT_CODE=$?
    log "ERROR" "auto_commit.py exited with code ${EXIT_CODE}"
fi

log "INFO" "run_auto_commit.sh finished (exit ${EXIT_CODE})"
log "INFO" "=========================================="

exit "${EXIT_CODE}"
