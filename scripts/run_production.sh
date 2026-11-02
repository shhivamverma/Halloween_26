#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "       Offline Ofrenda Keeper - Production Server"
echo "=========================================================="

export HF_HUB_OFFLINE=1
export DATA_DIR="./data"

BIND_HOST="127.0.0.1"
IS_LAN=0

if [ "$1" = "--lan" ] || [ "$ALLOW_LAN" = "1" ] || [ "$HOST" = "0.0.0.0" ]; then
    IS_LAN=1
fi

if [ "$IS_LAN" = "1" ]; then
    BIND_HOST="0.0.0.0"
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
    echo ""
    echo "==================================================================="
    echo " [SECURITY WARNING] LAN MODE ENABLED (0.0.0.0:8000)"
    echo "-------------------------------------------------------------------"
    echo " The application has NO BUILT-IN AUTHENTICATION, passwords, or"
    echo " access controls. ANYONE connected to your local Wi-Fi network can"
    echo " view, create, download, and delete family memorials, photos,"
    echo " and audio recordings."
    echo ""
    echo " Do NOT enable LAN mode on untrusted, public, or shared networks."
    echo "-------------------------------------------------------------------"
    echo " Local Computer:       http://127.0.0.1:8000"
    echo " Local Network (LAN):   http://${LOCAL_IP}:8000"
    echo "==================================================================="
    echo ""
else
    echo ""
    echo "[SECURE DEFAULT] Server listening on loopback interface only (127.0.0.1:8000)."
    echo "The application is NOT accessible from the local Wi-Fi / network."
    echo ""
    echo "Access in your browser: http://127.0.0.1:8000"
    echo ""
    echo "(To explicitly expose on local Wi-Fi, run: bash scripts/run_production.sh --lan)"
    echo "Press CTRL+C to stop the server."
    echo ""
fi

if [ "$1" = "--dry-run" ] || [ "$2" = "--dry-run" ]; then
    echo "[DRY RUN] Configured host: $BIND_HOST"
    exit 0
fi

if [ -f ".venv/bin/uvicorn" ]; then
    .venv/bin/uvicorn app.main:app --host "$BIND_HOST" --port 8000 --workers 1
else
    uvicorn app.main:app --host "$BIND_HOST" --port 8000 --workers 1
fi
