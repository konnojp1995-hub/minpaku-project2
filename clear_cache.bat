@echo off
REM Streamlitキャッシュ削除スクリプト（コマンドプロンプト版）

echo 🧹 Streamlitキャッシュ削除ツール
echo.

REM Step 1: Streamlitのキャッシュを削除
echo 🗑️  Streamlitのキャッシュを削除中...
if exist "%USERPROFILE%\.streamlit\cache" (
    rd /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
    echo    ✅ Streamlitキャッシュを削除しました
) else (
    echo    ℹ️  Streamlitキャッシュは存在しませんでした
)

REM Step 2: Pythonのコンパイルキャッシュを削除
echo.
echo 🗑️  Pythonのコンパイルキャッシュを削除中...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rd /s /q "%%d" 2>nul
)
echo    ✅ コンパイルキャッシュを削除しました

REM Step 3: 一時ファイルを削除
echo.
echo 🗑️  一時ファイルを削除中...
del /s /q temp_* 2>nul
echo    ✅ 一時ファイルを削除しました

REM Step 4: 完了メッセージ
echo.
echo ✅ キャッシュ削除が完了しました！
echo.
echo 🚀 アプリケーションを再起動するには:
echo    run.bat
echo.

pause

