#!/usr/bin/env bash
# ==============================================================================
# Pre-Academic-Year Automated Test Runner for SDS Container Image
#
# Tests:
#   1. In-container Python, R, Geospatial, Quarto, LaTeX, and Rootless UID/RW tests
#   2. Live host rootless container launch and JupyterLab web interface verification
#
# Usage:
#   # From host (runs full verification including live web interface test):
#   ./tests/run_tests.sh [IMAGE_NAME]
#
#   # Example:
#   ./tests/run_tests.sh jreades/sds:2026-arm64
#   ./tests/run_tests.sh ghcr.io/ucl-casa/sds:2026
#
#   # Directly inside a running container:
#   ./tests/run_tests.sh --in-container
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# If running directly inside the container:
if [[ "${1:-}" == "--in-container" ]]; then
    echo -e "${CYAN}🧪 Running test harness inside active container environment...${NC}\n"
    
    # Check if pytest is available, else install in user space or run python test
    if python -c "import pytest" 2>/dev/null; then
        pytest -v -s --color=yes "$SCRIPT_DIR/test_environment.py"
    else
        echo -e "${YELLOW}📦 Installing pytest in user cache to execute test harness...${NC}"
        pip install --quiet pytest
        pytest -v -s --color=yes "$SCRIPT_DIR/test_environment.py"
    fi
    exit 0
fi

echo -e "${BLUE}${BOLD}🚀 ====================================================== 🚀${NC}"
echo -e "${BLUE}${BOLD}   SDS Container Pre-Flight Verification & Live Tests    ${NC}"
echo -e "${BLUE}${BOLD}🚀 ====================================================== 🚀${NC}"

# Load configuration from docker/config.sh if available
if [[ -f "$REPO_ROOT/docker/config.sh" ]]; then
    # shellcheck source=../docker/config.sh
    . "$REPO_ROOT/docker/config.sh"
fi
TEST_OUTPUT_DIR="${TEST_OUTPUT_DIR:-tests/output}"
mkdir -p "$REPO_ROOT/$TEST_OUTPUT_DIR"

# Running from host via Podman or Docker
CONTAINER_CMD="podman"
if ! command -v podman >/dev/null 2>&1; then
    if command -v docker >/dev/null 2>&1; then
        CONTAINER_CMD="docker"
    else
        echo -e "${RED}❌ Error: Neither podman nor docker CLI found on host.${NC}" >&2
        exit 1
    fi
fi

IMAGE_NAME="${1:-localhost/jreades/sds:2026-arm64}"

IS_ROOTLESS="N/A (docker)"
EXTRA_TEST_FLAGS=()
if [[ "$CONTAINER_CMD" == "podman" ]]; then
    IS_ROOTLESS=$("$CONTAINER_CMD" info --format '{{.Host.Security.Rootless}}' 2>/dev/null || echo "unknown")
    if [[ "$OSTYPE" == "linux"* && "$IS_ROOTLESS" == "true" ]]; then
        EXTRA_TEST_FLAGS+=("--userns=keep-id:uid=1000,gid=100")
    fi
fi

echo -e "🐳 Container Runtime : ${BOLD}${CONTAINER_CMD}${NC}"
echo -e "🔒 Rootless Mode     : ${BOLD}${IS_ROOTLESS}${NC}"
echo -e "📦 Testing Image     : ${BOLD}${IMAGE_NAME}${NC}"
echo -e "📂 Working Directory : ${REPO_ROOT}"
echo -e "📁 Artifacts Output  : ${BOLD}${TEST_OUTPUT_DIR}${NC}"
echo -e "------------------------------------------------------\n"

# Verify image exists
if ! "$CONTAINER_CMD" image exists "$IMAGE_NAME" 2>/dev/null && ! "$CONTAINER_CMD" image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}📥 Image '${IMAGE_NAME}' not found locally. Attempting pull...${NC}"
    "$CONTAINER_CMD" pull "$IMAGE_NAME"
fi

# ------------------------------------------------------------------------------
# STEP 1: In-Container Verification Suite
# ------------------------------------------------------------------------------
echo -e "${BLUE}${BOLD}🧪 [Step 1/2] Running in-container environment verification suite...${NC}"

"$CONTAINER_CMD" run --rm \
    ${EXTRA_TEST_FLAGS[@]+"${EXTRA_TEST_FLAGS[@]}"} \
    -e TEST_OUTPUT_DIR="/home/jovyan/work/${TEST_OUTPUT_DIR}" \
    -v "${REPO_ROOT}:/home/jovyan/work:z" \
    -w /home/jovyan/work \
    "$IMAGE_NAME" \
    bash /home/jovyan/work/tests/run_tests.sh --in-container

echo -e "\n${GREEN}✅ [Step 1/2] All in-container environmental tests passed!${NC}\n"

# ------------------------------------------------------------------------------
# STEP 2: Live Rootless Web Interface & Port Forwarding Test
# ------------------------------------------------------------------------------
echo -e "${BLUE}${BOLD}🌐 [Step 2/2] Testing live rootless container & JupyterLab web server...${NC}"

TEST_PORT=18888
TEST_CONTAINER="sds-test-web-$$"

cleanup() {
    "$CONTAINER_CMD" rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo -e "🚀 Launching container in rootless mode on port ${BOLD}${TEST_PORT}${NC}..."
"$CONTAINER_CMD" run -d --name "$TEST_CONTAINER" \
    ${EXTRA_TEST_FLAGS[@]+"${EXTRA_TEST_FLAGS[@]}"} \
    -p "${TEST_PORT}:8888" \
    "$IMAGE_NAME" \
    start.sh jupyter lab --LabApp.password='' --ServerApp.password='' --NotebookApp.token='' >/dev/null

echo -e "⏳ Waiting for JupyterLab web interface to become ready at http://127.0.0.1:${TEST_PORT}/lab ..."
SERVER_READY=false
HTTP_STATUS="000"

for attempt in {1..35}; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${TEST_PORT}/lab" 2>/dev/null || echo "000")
    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "302" ]]; then
        SERVER_READY=true
        break
    fi
    sleep 1
done

if [[ "$SERVER_READY" == "true" ]]; then
    PAGE_TITLE=$(curl -s "http://127.0.0.1:${TEST_PORT}/lab" 2>/dev/null | grep -io "<title>[^<]*</title>" | head -n 1 || echo "<title>JupyterLab</title>")
    echo -e "${GREEN}✅ HTTP ${HTTP_STATUS} OK — JupyterLab web server is active and responding!${NC}"
    echo -e "${GREEN}📡 Verified Page Header : ${BOLD}${PAGE_TITLE}${NC}"
    echo -e "${GREEN}🔒 Verified Rootless Port Forwarding : 127.0.0.1:${TEST_PORT} -> container:8888${NC}"
else
    echo -e "${RED}❌ Error: Web interface did not respond within 35 seconds (HTTP: ${HTTP_STATUS}).${NC}" >&2
    echo -e "${YELLOW}Container Logs:${NC}" >&2
    "$CONTAINER_CMD" logs "$TEST_CONTAINER" | tail -n 25 >&2
    exit 1
fi

echo -e "🧹 Stopping and removing test container..."
cleanup
trap - EXIT INT TERM

# Display generated artifacts if any were created
if [[ -d "$REPO_ROOT/$TEST_OUTPUT_DIR" ]] && [[ $(ls -A "$REPO_ROOT/$TEST_OUTPUT_DIR" 2>/dev/null) ]]; then
    echo -e "\n${CYAN}${BOLD}📁 Generated Graphical & Document Test Artifacts (${TEST_OUTPUT_DIR}):${NC}"
    for f in "$REPO_ROOT/$TEST_OUTPUT_DIR"/*; do
        if [[ -f "$f" ]]; then
            SIZE=$(ls -lh "$f" | awk '{print $5}')
            BASE=$(basename "$f")
            EXT="${BASE##*.}"
            ICON="📄"
            case "$EXT" in
                png|jpg|jpeg|svg) ICON="🖼️" ;;
                pdf)              ICON="📑" ;;
                html|htm)         ICON="🌐" ;;
                tex)              ICON="📝" ;;
                ipynb)            ICON="📓" ;;
            esac
            echo -e "   ${ICON} ${BASE} ${BOLD}(${SIZE})${NC}"
        fi
    done
fi

echo -e "\n${GREEN}${BOLD}🎉 ====================================================== 🎉${NC}"
echo -e "${GREEN}${BOLD}   All Pre-Flight Environmental & Rootless Tests Passed! ${NC}"
echo -e "${GREEN}${BOLD}🎉 ====================================================== 🎉${NC}"

