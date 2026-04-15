#!/usr/bin/env bash

set -euo pipefail

# Local launcher for the Streamlit frontend.
#
# Required application environment variables (typically from .env):
# - ENV
# - API_BASE_URL
# - GOOGLE_CLIENT_ID
# - REDIRECT_URI
#
# Optional script-specific variables:
# - STREAMLIT_PORT (default: 8080)
# - APP_ENTRYPOINT (default: src/app.py)
# - ENV_FILE (default: .env)
# - RESTART_STREAMLIT (default: 0, set to 1 to force restart/log out session)

STREAMLIT_PORT="${STREAMLIT_PORT:-8080}"
APP_ENTRYPOINT="${APP_ENTRYPOINT:-src/app.py}"
ENV_FILE="${ENV_FILE:-.env}"


kill_previous_streamlit() {
  echo "Checking for existing Streamlit process on port ${STREAMLIT_PORT}..."
  local pid
  pid="$(lsof -ti:"${STREAMLIT_PORT}" || true)"
  if [[ -z "${pid}" ]]; then
    echo "No Streamlit process found on port ${STREAMLIT_PORT}."
    return
  fi

  echo "Stopping existing process (PID: ${pid})..."
  kill "${pid}" || true
  sleep 1
  if lsof -ti:"${STREAMLIT_PORT}" >/dev/null 2>&1; then
    echo "Process is still running, sending SIGKILL..."
    kill -9 "${pid}" || true
  fi
}


load_env() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Environment file '${ENV_FILE}' was not found."
    exit 1
  fi

  echo "Loading environment variables from ${ENV_FILE}..."
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
}


validate_required_env() {
  local required_vars=("ENV" "API_BASE_URL" "GOOGLE_CLIENT_ID" "REDIRECT_URI")
  local missing=()

  for key in "${required_vars[@]}"; do
    if [[ -z "${!key:-}" ]]; then
      missing+=("${key}")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    echo "Missing required environment variables: ${missing[*]}"
    exit 1
  fi
}


run_dev() {
  if lsof -ti:"${STREAMLIT_PORT}" >/dev/null 2>&1; then
    if [[ "${RESTART_STREAMLIT:-0}" != "1" ]]; then
      echo "Streamlit is already running on port ${STREAMLIT_PORT}."
      echo "Reusing existing session (no logout). Set RESTART_STREAMLIT=1 to force restart."
      return
    fi
    kill_previous_streamlit
  fi

  load_env
  validate_required_env
  echo "Starting Streamlit on port ${STREAMLIT_PORT} (${ENV})..."
  PYTHONPATH="${PWD}" uv run streamlit run "${APP_ENTRYPOINT}" \
    --server.port "${STREAMLIT_PORT}" \
    --server.headless=true
}


run_dev
