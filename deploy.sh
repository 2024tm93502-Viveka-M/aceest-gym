#!/bin/bash
# deploy.sh — runs ON the BITS VM
set -e

DEPLOY_DIR="/opt/aceest-gym"
VENV_DIR="${DEPLOY_DIR}/venv"
RELEASES_DIR="${DEPLOY_DIR}/releases"
CURRENT_LINK="${DEPLOY_DIR}/current"
PACKAGE="${PACKAGE:-aceest-gym.tar.gz}"
RELEASE_NAME=$(date +%Y%m%d_%H%M%S)
RELEASE_PATH="${RELEASES_DIR}/${RELEASE_NAME}"

echo "=== ACEest Deploy: ${RELEASE_NAME} ==="

# Create directory structure
mkdir -p "${RELEASES_DIR}" "${DEPLOY_DIR}"

# Backup current as 'previous' for rollback
if [ -L "${CURRENT_LINK}" ]; then
    PREV=$(readlink "${CURRENT_LINK}")
    echo "Previous release: ${PREV}"
    ln -sfn "${PREV}" "${DEPLOY_DIR}/previous"
fi

# Extract new release
mkdir -p "${RELEASE_PATH}"
tar -xzf "/tmp/${PACKAGE}" -C "${RELEASE_PATH}"

# Setup virtualenv (only once)
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip -q
"${VENV_DIR}/bin/pip" install -r "${RELEASE_PATH}/requirements.txt" -q

# Symlink current → new release
ln -sfn "${RELEASE_PATH}" "${CURRENT_LINK}"

echo "=== Deploy complete: ${CURRENT_LINK} -> ${RELEASE_PATH} ==="

# Keep only last 5 releases
ls -dt "${RELEASES_DIR}"/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
