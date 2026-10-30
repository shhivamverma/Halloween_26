#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "       Offline Ofrenda Keeper - Production Server"
echo "=========================================================="

export HF_HUB_OFFLINE=1
export DATA_DIR="./data"

LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

echo ""
echo "Server starting on all network interfaces (0.0.0.0:8000)..."
echo "Local Computer:       http://localhost:8000"
echo "Local Network (LAN):  http://${LOCAL_IP}:8000"
echo ""
echo "Family members on the same Wi-Fi can connect using the LAN URL above."
echo "Press CTRL+C to stop the server."
echo ""

if [ -f ".venv/bin/uvicorn" ]; then
    .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
else
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
fi
