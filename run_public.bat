@echo off
REM Batch Script: Run Streamlit app with ngrok tunnel for public access
REM Usage: run_public.bat
REM 
REM Prerequisites:
REM 1. Install ngrok: https://ngrok.com/download
REM 2. Sign up for a free ngrok account and get your authtoken
REM 3. Configure ngrok: ngrok config add-authtoken YOUR_TOKEN

echo ========================================
echo Streamlit Public Access Setup
echo ========================================
echo.

REM Check if ngrok exists
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: ngrok is not installed or not in PATH
    echo.
    echo Please install ngrok:
    echo   1. Download from https://ngrok.com/download
    echo   2. Extract and add to PATH, or place ngrok.exe in this directory
    echo   3. Sign up for free account: https://dashboard.ngrok.com/signup
    echo   4. Configure: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Starting Streamlit app...
echo.
echo IMPORTANT: Keep this window open!
echo.
echo Starting ngrok tunnel in a new window...
echo You will see the public URL in the ngrok window.
echo.

REM Start Streamlit in a new window
start "Streamlit App" cmd /k "call venv\Scripts\activate.bat && streamlit run src/main.py --server.address=0.0.0.0 --server.port=8501"

REM Wait a moment for Streamlit to start
timeout /t 3 /nobreak >nul

REM Start ngrok in a new window
start "ngrok Tunnel" cmd /k "ngrok http 8501"

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Streamlit is running at: http://localhost:8501
echo.
echo Check the ngrok window for your public URL (usually https://xxxx-xx-xx-xx-xx.ngrok-free.app)
echo Or visit: http://localhost:4040 (ngrok dashboard)
echo.
echo Press any key to stop both services...
pause >nul

echo.
echo Stopping services...
taskkill /FI "WindowTitle eq Streamlit App*" /F >nul 2>&1
taskkill /FI "WindowTitle eq ngrok Tunnel*" /F >nul 2>&1
taskkill /F /IM ngrok.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1
echo Cleanup complete!
