@echo off
setlocal

echo ==========================================================
echo        Offline Ofrenda Keeper - Production Server
echo ==========================================================

REM Set environment flags
set HF_HUB_OFFLINE=1
set DATA_DIR=./data

REM Check if LAN mode is explicitly requested via --lan argument or ALLOW_LAN=1
set BIND_HOST=127.0.0.1
set IS_LAN=0

if "%1"=="--lan" set IS_LAN=1
if "%1"=="/lan" set IS_LAN=1
if "%ALLOW_LAN%"=="1" set IS_LAN=1
if "%HOST%"=="0.0.0.0" set IS_LAN=1

if "%IS_LAN%"=="1" (
    set BIND_HOST=0.0.0.0
    for /f "tokens=4" %%a in ('route print ^| find " 0.0.0.0"') do set LOCAL_IP=%%a
    echo.
    echo ===================================================================
    echo  [SECURITY WARNING] LAN MODE ENABLED (0.0.0.0:8000)
    echo -------------------------------------------------------------------
    echo  The application has NO BUILT-IN AUTHENTICATION, passwords, or
    echo  access controls. ANYONE connected to your local Wi-Fi network can
    echo  view, create, download, and delete family memorials, photos,
    echo  and audio recordings.
    echo.
    echo  Do NOT enable LAN mode on untrusted, public, or shared networks.
    echo -------------------------------------------------------------------
    echo  Local Computer:       http://127.0.0.1:8000
    echo  Local Network (LAN):   http://%LOCAL_IP%:8000
    echo ===================================================================
    echo.
) else (
    echo.
    echo [SECURE DEFAULT] Server listening on loopback interface only (127.0.0.1:8000).
    echo The application is NOT accessible from the local Wi-Fi / network.
    echo.
    echo Access in your browser: http://127.0.0.1:8000
    echo.
    echo (To explicitly expose on local Wi-Fi, run: run_production.bat --lan)
    echo Press CTRL+C to stop the server.
    echo.
)

if "%1"=="--dry-run" (
    echo [DRY RUN] Configured host: %BIND_HOST%
    exit /b 0
)
if "%2"=="--dry-run" (
    echo [DRY RUN] Configured host: %BIND_HOST%
    exit /b 0
)

if exist .venv\Scripts\uvicorn.exe (
    .venv\Scripts\uvicorn.exe app.main:app --host %BIND_HOST% --port 8000 --workers 1
) else (
    uvicorn app.main:app --host %BIND_HOST% --port 8000 --workers 1
)

endlocal
