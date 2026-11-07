# Free port 8501 and start Streamlit from the project venv.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Missing .venv. Create it with: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
}

$conns = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    Write-Host "Stopping PID $($c.OwningProcess) on port 8501..."
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}

# Also clear a stale 8502 instance from earlier runs.
$conns8502 = Get-NetTCPConnection -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns8502) {
    Write-Host "Stopping PID $($c.OwningProcess) on port 8502..."
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1
Write-Host "Starting Streamlit on http://localhost:8501"
& $python -m streamlit run (Join-Path $Root "app.py") --server.port 8501
