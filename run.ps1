# PowerShell Script: Activate virtual environment and run Streamlit app
# Usage: .\run.ps1

$ErrorActionPreference = 'Stop'

Write-Host 'Activating virtual environment...' -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
    Write-Host 'Starting Streamlit app...' -ForegroundColor Green
    Write-Host 'Browser will open at http://localhost:8501' -ForegroundColor Cyan
    Write-Host 'Press Ctrl+C to stop the app' -ForegroundColor Yellow
    Write-Host ''
    streamlit run src/main.py
} else {
    Write-Host 'Error: Failed to activate virtual environment' -ForegroundColor Red
    Write-Host 'Please run manually:' -ForegroundColor Yellow
    Write-Host '  .\venv\Scripts\Activate.ps1' -ForegroundColor Yellow
    Write-Host '  streamlit run src/main.py' -ForegroundColor Yellow
}
