# OpenDots PowerShell Launcher
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "   OPENDOTS - AUTONOMOUS AI AGENT WORKSPACE (COPILOTKIT + OMNIROUTE)          " -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

$env:Path = "C:\Program Files\nodejs;C:\Users\Arush\AppData\Roaming\npm;" + $env:Path

$openDotsDir = Join-Path $PSScriptRoot "OpenDots"
Set-Location $openDotsDir

if (-not (Test-Path ".env")) {
    Write-Host "[*] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Check OmniRoute port
$omniPort = Get-NetTCPConnection -LocalPort 20128 -ErrorAction SilentlyContinue
if (-not $omniPort) {
    Write-Host "[!] OmniRoute Gateway is not currently active on port 20128." -ForegroundColor Yellow
    Write-Host "[*] Launching OmniRoute in the background..." -ForegroundColor Gray
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c omniroute start" -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[+] OmniRoute Gateway is active on http://localhost:20128" -ForegroundColor Green
}

Write-Host "[*] Starting OpenDots dev server..." -ForegroundColor Cyan
Write-Host "    - Web Workspace: http://localhost:5173" -ForegroundColor White
Write-Host "    - API Gateway:   http://localhost:4310" -ForegroundColor White

Start-Process "http://localhost:5173"
npm run dev
