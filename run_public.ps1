# PowerShell Script: Run Streamlit app with ngrok tunnel for public access
# Usage: .\run_public.ps1
# 
# Prerequisites:
# 1. Install ngrok: https://ngrok.com/download
# 2. Sign up for a free ngrok account and get your authtoken
# 3. Configure ngrok: ngrok config add-authtoken YOUR_TOKEN
# 
# This script will:
# 1. Start Streamlit app on localhost:8501
# 2. Create an ngrok tunnel to expose it to the internet
# 3. Display the public URL

$ErrorActionPreference = 'Stop'

Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Streamlit Public Access Setup' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# Check if ngrok is installed
$ngrokExists = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokExists) {
    Write-Host 'Error: ngrok is not installed or not in PATH' -ForegroundColor Red
    Write-Host ''
    Write-Host 'Please install ngrok:' -ForegroundColor Yellow
    Write-Host '  1. Download from https://ngrok.com/download' -ForegroundColor Yellow
    Write-Host '  2. Extract and add to PATH, or place ngrok.exe in this directory' -ForegroundColor Yellow
    Write-Host '  3. Sign up for free account: https://dashboard.ngrok.com/signup' -ForegroundColor Yellow
    Write-Host '  4. Configure: ngrok config add-authtoken YOUR_TOKEN' -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

Write-Host 'Activating virtual environment...' -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Write-Host 'Error: Failed to activate virtual environment' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host 'Starting Streamlit app in background...' -ForegroundColor Green

# Start Streamlit in background
$streamlitJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    streamlit run src/main.py --server.address=0.0.0.0 --server.port=8501 --server.enableCORS=false
}

# Wait a moment for Streamlit to start
Start-Sleep -Seconds 3

Write-Host 'Starting ngrok tunnel...' -ForegroundColor Green
Write-Host ''

# Start ngrok tunnel
$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http", "8501" -NoNewWindow -PassThru

# Wait a moment for ngrok to start
Start-Sleep -Seconds 2

# Try to get ngrok public URL
try {
    $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
    if ($ngrokApi.tunnels -and $ngrokApi.tunnels.Count -gt 0) {
        $publicUrl = $ngrokApi.tunnels[0].public_url
        Write-Host '========================================' -ForegroundColor Green
        Write-Host 'SUCCESS! Your app is now public:' -ForegroundColor Green
        Write-Host $publicUrl -ForegroundColor Cyan
        Write-Host '========================================' -ForegroundColor Green
        Write-Host ''
        Write-Host 'You can also check ngrok dashboard at:' -ForegroundColor Yellow
        Write-Host 'http://localhost:4040' -ForegroundColor Cyan
        Write-Host ''
        Write-Host 'Press Ctrl+C to stop both Streamlit and ngrok' -ForegroundColor Yellow
        Write-Host ''
    } else {
        Write-Host 'Warning: Could not retrieve ngrok public URL automatically' -ForegroundColor Yellow
        Write-Host 'Please check ngrok dashboard at http://localhost:4040' -ForegroundColor Cyan
    }
} catch {
    Write-Host 'Warning: Could not retrieve ngrok public URL automatically' -ForegroundColor Yellow
    Write-Host 'Please check ngrok dashboard at http://localhost:4040' -ForegroundColor Cyan
}

# Wait for user to stop
try {
    Write-Host 'Press Ctrl+C to stop...' -ForegroundColor Yellow
    while ($true) {
        Start-Sleep -Seconds 1
        if (Get-Job -Id $streamlitJob.Id -ErrorAction SilentlyContinue) {
            $jobState = (Get-Job -Id $streamlitJob.Id).State
            if ($jobState -eq 'Failed' -or $jobState -eq 'Completed') {
                Write-Host 'Streamlit job stopped unexpectedly' -ForegroundColor Red
                break
            }
        }
    }
} catch {
    Write-Host ''
    Write-Host 'Stopping...' -ForegroundColor Yellow
} finally {
    # Cleanup
    if (Get-Job -Id $streamlitJob.Id -ErrorAction SilentlyContinue) {
        Stop-Job -Id $streamlitJob.Id
        Remove-Job -Id $streamlitJob.Id
    }
    if ($ngrokProcess -and -not $ngrokProcess.HasExited) {
        Stop-Process -Id $ngrokProcess.Id -Force
    }
    Write-Host 'Cleanup complete' -ForegroundColor Green
}
