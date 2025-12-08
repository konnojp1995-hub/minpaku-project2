@echo off
REM 仮想環境を有効化してStreamlitアプリを起動
REM 使用方法: run.bat

echo 仮想環境を有効化しています...
call venv\Scripts\activate.bat

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Streamlitアプリを起動しています...
    echo ブラウザで http://localhost:8501 が自動で開きます
    echo アプリを停止する場合は Ctrl+C を押してください
    echo.
    streamlit run src/main.py
) else (
    echo.
    echo エラー: 仮想環境の有効化に失敗しました
    echo 手動で以下を実行してください:
    echo   venv\Scripts\activate.bat
    echo   streamlit run src/main.py
    pause
)



