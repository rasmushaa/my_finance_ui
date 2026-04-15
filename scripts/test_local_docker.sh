#!/usr/bin/env bash

# Script to test Docker build locally before CI/CD deployment.
# Adapted for the my_finance_ui Streamlit frontend project.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-my-finance-ui-test}"
IMAGE_NAME_TAG="${IMAGE_NAME}:latest"
CONTAINER_NAME="${CONTAINER_NAME:-${IMAGE_NAME}-local}"
PORT="${PORT:-8080}"
ENV="${ENV:-dev}"
ENV_FILE="${ENV_FILE:-.env}"

echo -e "${YELLOW}Testing Docker build locally${NC}"
echo "Environment: ${ENV}"
echo "Env file: ${ENV_FILE}"
echo "Image: ${IMAGE_NAME_TAG}"
echo "Container: ${CONTAINER_NAME}"

# Check for .env file
if [[ ! -f "${ENV_FILE}" ]]; then
  echo -e "${RED}.env file not found at '${ENV_FILE}'. Create one according to README/.env.example.${NC}"
  exit 1
fi

require_env_key() {
  local key="$1"
  if ! grep -Eq "^[[:space:]]*${key}=" "${ENV_FILE}"; then
    echo -e "${RED}Missing required key '${key}' in ${ENV_FILE}.${NC}"
    exit 1
  fi
}

require_env_key "ENV"
require_env_key "API_BASE_URL"
require_env_key "GOOGLE_CLIENT_ID"
require_env_key "REDIRECT_URI"

# Ensure Docker Desktop / daemon is running; open it if not and wait until ready.
ensure_docker_running() {
  local timeout=120
  local interval=2
  local waited=0

  if docker info >/dev/null 2>&1; then
    return 0
  fi

  echo "Docker daemon not available."
  if command -v open >/dev/null 2>&1; then
    echo "Opening Docker.app..."
    open -a Docker || true
  fi

  printf "Waiting for Docker to be ready"
  while ! docker info >/dev/null 2>&1; do
    sleep "${interval}"
    waited=$((waited + interval))
    printf "."
    if [[ "${waited}" -ge "${timeout}" ]]; then
      echo
      echo "Timed out after ${timeout}s waiting for Docker to start."
      return 1
    fi
  done
  echo
  echo "Docker is ready (waited ${waited}s)."
  return 0
}

if ! ensure_docker_running; then
  echo -e "${RED}Cannot connect to Docker daemon. Start Docker and retry.${NC}"
  exit 1
fi

# Build Docker image
echo -e "\n${YELLOW}1. Building Docker image ${IMAGE_NAME_TAG}...${NC}"
DOCKER_BUILDKIT=1 docker build \
  --build-arg ENV="${ENV}" \
  -t "${IMAGE_NAME_TAG}" \
  .
echo -e "${GREEN}Docker build successful.${NC}"

# Stop and remove any existing container with the same name
if docker ps -aq -f name="^${CONTAINER_NAME}$" | grep -q .; then
  echo -e "\n${YELLOW}2. Removing existing container ${CONTAINER_NAME}...${NC}"
  docker rm -f "${CONTAINER_NAME}"
fi

# Run the Docker container
# Container listens on 8080; host port is configurable via PORT.
echo -e "\n${YELLOW}3. Running container ${CONTAINER_NAME} from image ${IMAGE_NAME_TAG}...${NC}"
docker run -d \
  --env-file "${ENV_FILE}" \
  -p "${PORT}:8080" \
  --name "${CONTAINER_NAME}" \
  "${IMAGE_NAME_TAG}"

echo -e "\n${GREEN}4. Container ${CONTAINER_NAME} started. Access app at http://localhost:${PORT}${NC}"

# Wait a moment and check if container is running
sleep 3
if docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo -e "${GREEN}Container is running successfully.${NC}"
  echo -e "${YELLOW}Recent logs:${NC}"
  docker logs "${CONTAINER_NAME}" 2>&1 | tail -10
else
  echo -e "${RED}Container failed to start. Logs:${NC}"
  docker logs "${CONTAINER_NAME}" 2>&1 || true
  exit 1
fi

echo
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs: docker logs ${CONTAINER_NAME} -f"
echo "  Stop container: docker stop ${CONTAINER_NAME}"
echo "  Remove container: docker rm -f ${CONTAINER_NAME}"
echo "  Remove test image: docker rmi ${IMAGE_NAME_TAG}"
echo
echo -e "${GREEN}Docker local test completed successfully.${NC}"
