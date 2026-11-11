# RouteWise Windows helper — start/stop/status without duplicate servers.
param(
    [Parameter(Position = 0)]
    [ValidateSet("status", "backend", "frontend", "lab-status", "lab-deploy", "lab-destroy", "check")]
    [string]$Command = "status"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "backend"))) {
    $Root = $PSScriptRoot + "\.."
}
$Root = (Resolve-Path $Root).Path

function Port-Owner([int]$Port) {
    $lines = netstat -ano | Select-String ":$Port\s+.*LISTENING"
    foreach ($line in $lines) {
        if ($line -match "\s+(\d+)\s*$") {
            return [int]$Matches[1]
        }
    }
    return $null
}

function Show-Status {
    $be = Port-Owner 8000
    $fe = Port-Owner 5173
    Write-Host "Backend  :8000  $(if ($be) { "PID $be" } else { "down" })"
    Write-Host "Frontend :5173  $(if ($fe) { "PID $fe" } else { "down" })"
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 3
        Write-Host "Health   : $($h.status) $($h.app) $($h.version)"
    } catch {
        Write-Host "Health   : unreachable"
    }
    wsl -e bash -lc "clab version 2>/dev/null | head -3; docker ps --filter name=clab-routewise --format '{{.Names}} {{.Status}}'" 2>$null
}

switch ($Command) {
    "status" { Show-Status }
    "check" {
        wsl -e bash -lc "cd /mnt/c/Users/deepa/cn && bash scripts/check_environment.sh"
    }
    "backend" {
        $pid = Port-Owner 8000
        if ($pid) {
            Write-Host "Backend already listening on :8000 (PID $pid) — not starting a duplicate."
            break
        }
        Set-Location (Join-Path $Root "backend")
        Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WindowStyle Hidden
        Write-Host "Backend start requested."
    }
    "frontend" {
        $pid = Port-Owner 5173
        if ($pid) {
            Write-Host "Frontend already listening on :5173 (PID $pid) — not starting a duplicate."
            break
        }
        Set-Location (Join-Path $Root "frontend")
        Start-Process -FilePath "npm" -ArgumentList "run","dev","--","--host","127.0.0.1","--port","5173" -WindowStyle Hidden
        Write-Host "Frontend start requested."
    }
    "lab-status" {
        wsl -e bash -lc "docker ps --filter name=clab-routewise --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
    }
    "lab-deploy" {
        wsl -e bash -lc "cd /mnt/c/Users/deepa/cn/lab && clab deploy -t routewise.clab.yml"
    }
    "lab-destroy" {
        wsl -e bash -lc "cd /mnt/c/Users/deepa/cn/lab && clab destroy -t routewise.clab.yml --cleanup"
    }
}
