@echo off
title OmniVoice API Server Launcher
color 0B
setlocal enabledelayedexpansion

echo.
echo  ================================================================
echo    OmniVoice API Server Launcher v1.1.0
echo    Server: omnivoice-api-server (Phase 6: VoiceID Registry)
echo    OmniVoice model: pinned to v0.2.0
echo  ================================================================
echo.

:: ─── Step 1: Check Python ──────────────────────────────────────────────
echo [1/5] Kiem tra Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo  [ERROR] Python chua cai hoac chua co trong PATH.
    echo  Tai Python 3.10-3.12 tai https://www.python.org/downloads/
    echo  Khi cai NHO tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        %%v OK
echo.

:: ─── Step 2: Check venv ──────────────────────────────────────────────
echo [2/5] Kiem tra virtual environment...
if not exist "%~dp0venv\Scripts\activate.bat" (
    color 0C
    echo  [ERROR] Khong tim thay venv\Scripts\activate.bat
    echo  Vui long chay setup_and_run.bat truoc de cai dat dependencies.
    echo.
    pause
    exit /b 1
)
echo        venv OK
echo.

:: ─── Step 3: Activate venv + version check ────────────────────────────
echo [3/5] Kich hoat venv va kiem tra version...
call "%~dp0venv\Scripts\activate.bat" >nul 2>&1
echo        activated.

:: Check omnivoice version
python -c "import omnivoice; print('        omnivoice:', omnivoice.__version__)" 2>nul
if %errorlevel% neq 0 (
    color 0E
    echo  [WARN] Khong import duoc omnivoice. Co the can cai lai:
    echo         pip install -r requirements.txt
    echo.
)

:: Quick CUDA check
python -c "import torch; ok=torch.cuda.is_available(); name=torch.cuda.get_device_name(0) if ok else 'None'; print('        [GPU]', name if ok else '[GPU] Not available - se chay CPU')" 2>nul
echo.

:: ─── Step 4: Check voices dir + registry ──────────────────────────────
echo [4/5] Kiem tra voices/ va voice_registry.json...

if not exist "%~dp0voices" mkdir "%~dp0voices"
if not exist "%~dp0voices\NUL" (
    echo        voices/ OK (tao moi neu chua co)
) else (
    echo        voices/ OK
)

if not exist "%~dp0voice_registry.json" (
    color 0E
    echo  [WARN] voice_registry.json chua ton tai.
    echo         Server se khoi dong nhung /v1/catalog se tra ve 0 voice.
    echo         Copy file mau tu setup_and_run.bat hoac tao bang POST /v1/voices.
) else (
    echo        voice_registry.json OK
)
echo.

:: ─── Step 5: Choose host + port ───────────────────────────────────────
:: Set default port TRUOC khi in menu (de %PORT% khong bi trong)
if "%OMNIVOICE_PORT%"=="" set "OMNIVOICE_PORT=8088"
if "%PORT%"=="" set "PORT=8088"

echo [5/5] Chon che do khoi dong:
echo.
echo   [1] Local only    - http://127.0.0.1:%PORT%   (chi may nay)
echo   [2] LAN network   - http://0.0.0.0:%PORT%     (cho App khac trong mang)
echo   [3] Custom        - tu nhap IP va port
echo   [Q] Thoat
echo.

set /p choice="Nhap lua chon (1/2/3/Q): "
if /i "%choice%"=="Q" goto :quit
goto :parse_choice

:parse_choice
if "%choice%"=="1" (
    set "OMNIVOICE_HOST=127.0.0.1"
    set "PORT=8088"
    goto :launch
)
if "%choice%"=="2" (
    set "OMNIVOICE_HOST=0.0.0.0"
    set "PORT=8088"
    :: Show LAN IP for user reference
    echo.
    echo        LAN IP cua may nay:
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        echo          http://%%a:8088
    )
    echo.
    goto :launch
)
if "%choice%"=="3" (
    set /p OMNIVOICE_HOST="Nhap host/IP (mac dinh 127.0.0.1): "
    if "%OMNIVOICE_HOST%"=="" set "OMNIVOICE_HOST=127.0.0.1"
    set /p PORT="Nhap port (mac dinh 8088): "
    if "%PORT%"=="" set "PORT=8088"
    goto :launch
)

:: Invalid choice
color 0C
echo  [ERROR] Lua chon khong hop le: %choice%
pause
exit /b 1

:quit
echo        Bye!
exit /b 0

:launch

:: ─── Kill any process on the port ─────────────────────────────────────
echo.
echo        Kiem tra port %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING 2^>nul') do (
    echo        Port %PORT% dang dung boi PID %%a - dang kill...
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: ─── Launch server ────────────────────────────────────────────────────
echo.
echo  ================================================================
echo    Starting OmniVoice server on http://%OMNIVOICE_HOST%:%PORT%
echo    Web UI:  http://%OMNIVOICE_HOST%:%PORT%/
echo    Health:  http://%OMNIVOICE_HOST%:%PORT%/health
echo    Version: http://%OMNIVOICE_HOST%:%PORT%/v1/version
echo    Catalog: http://%OMNIVOICE_HOST%:%PORT%/v1/catalog
echo    ^(Ctrl+C de dung server^)
echo  ================================================================
echo.

set "OMNIVOICE_HOST=%OMNIVOICE_HOST%"
set "OMNIVOICE_PORT=%PORT%"

cd /d "%~dp0app"
"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host %OMNIVOICE_HOST% --port %PORT% --log-level info

echo.
echo  [INFO] Server da dung.
pause