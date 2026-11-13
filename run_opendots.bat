@echo off
title OpenDots // Autonomous AI Coworkers Workspace
color 0b

echo ==============================================================================
echo    OPENDOTS - AUTONOMOUS AI AGENT WORKSPACE (COPILOTKIT + OMNIROUTE)
echo ==============================================================================
echo.

set "PATH=C:\Program Files\nodejs;C:\Users\Arush\AppData\Roaming\npm;%PATH%"

cd /d "%~dp0OpenDots"

echo [*] Checking OpenDots environment (.env)...
if not exist ".env" (
    echo [-] .env not found. Creating from .env.example...
    copy .env.example .env
)

echo [*] Verifying OmniRoute AI Gateway on port 20128...
netstat -ano | findstr ":20128" >nul
if %errorlevel% neq 0 (
    echo [!] OmniRoute Gateway is not currently active on port 20128.
    echo [*] Starting OmniRoute Gateway in background...
    start /min "OmniRoute Gateway" cmd /c "omniroute start"
    timeout /t 3 >nul
) else (
    echo [+] OmniRoute Gateway is active on http://localhost:20128.
)

echo.
echo [*] Starting OpenDots dev server (UI: http://127.0.0.1:5173, API: http://127.0.0.1:4310)...
echo [*] Press Ctrl+C anytime to stop.
echo.

start "" "http://localhost:5173"
npm run dev

pause
