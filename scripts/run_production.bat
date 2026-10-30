@echo off
setlocal

echo ==========================================================
echo        Offline Ofrenda Keeper - Production Server
echo ==========================================================

REM Set environment flags
set HF_HUB_OFFLINE=1
set DATA_DIR=./data

REM Find local IP address
for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set LOCAL_IP=%%a

echo.
echo Server starting on all network interfaces (0.0.0.0:8000)...
echo.
echo Local Computer:       http://localhost:8000
echo Local Network (LAN):  http://%LOCAL_IP%:8000
echo.
echo Family members on the same Wi-Fi can connect using the LAN URL above.
echo Press CTRL+C to stop the server.
echo.

if exist .venv\Scripts\uvicorn.exe (
    .venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --workers 2
) else (
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
)

endlocal

