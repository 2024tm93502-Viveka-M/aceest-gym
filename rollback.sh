#!/bin/bash
# rollback.sh — runs ON the BITS VM
# Switches 'current' symlink back to 'previous' release

DEPLOY_DIR="/opt/aceest-gym"
CURRENT_LINK="${DEPLOY_DIR}/current"
PREVIOUS_LINK="${DEPLOY_DIR}/previous"

echo "=== ACEest ROLLBACK initiated ==="

if [ ! -L "${PREVIOUS_LINK}" ]; then
    echo "ERROR: No previous release found. Cannot rollback."
    exit 1
fi

PREV_PATH=$(readlink "${PREVIOUS_LINK}")

if [ ! -d "${PREV_PATH}" ]; then
    echo "ERROR: Previous release directory missing: ${PREV_PATH}"
    exit 1
fi

echo "Rolling back to: ${PREV_PATH}"
ln -sfn "${PREV_PATH}" "${CURRENT_LINK}"
echo "=== Rollback complete: current -> ${PREV_PATH} ==="
