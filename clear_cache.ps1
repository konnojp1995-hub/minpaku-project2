# Streamlitキャッシュ削除スクリプト（PowerShell版）

Write-Host "🧹 Streamlitキャッシュ削除ツール" -ForegroundColor Cyan
Write-Host ""

# Step 1: 実行中のアプリケーションがないか確認
Write-Host "📋 実行中のアプリケーションを確認中..." -ForegroundColor Yellow
$streamlitProcesses = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
if ($streamlitProcesses) {
    Write-Host "⚠️  実行中のStreamlitプロセスを検出しました" -ForegroundColor Yellow
    Write-Host "   先にアプリケーションを停止してください（Ctrl+C）" -ForegroundColor Yellow
    $continue = Read-Host "続行しますか？ (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "❌ キャッシュ削除をキャンセルしました" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Streamlitのキャッシュを削除
Write-Host ""
Write-Host "🗑️  Streamlitのキャッシュを削除中..." -ForegroundColor Yellow
$streamlitCachePath = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $streamlitCachePath) {
    Remove-Item -Path $streamlitCachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Streamlitキャッシュを削除しました: $streamlitCachePath" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  Streamlitキャッシュは存在しませんでした" -ForegroundColor Gray
}

# Step 3: Pythonのコンパイルキャッシュを削除
Write-Host ""
Write-Host "🗑️  Pythonのコンパイルキャッシュを削除中..." -ForegroundColor Yellow
$pycacheCount = 0
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $pycacheCount++
}
if ($pycacheCount -gt 0) {
    Write-Host "   ✅ $pycacheCount 個の __pycache__ ディレクトリを削除しました" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  コンパイルキャッシュは存在しませんでした" -ForegroundColor Gray
}

# Step 4: 一時ファイルを削除
Write-Host ""
Write-Host "🗑️  一時ファイルを削除中..." -ForegroundColor Yellow
$tempFiles = Get-ChildItem -Path . -Filter "temp_*" -File -Recurse -ErrorAction SilentlyContinue
if ($tempFiles) {
    $tempFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ $($tempFiles.Count) 個の一時ファイルを削除しました" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  一時ファイルは存在しませんでした" -ForegroundColor Gray
}

# Step 5: 完了メッセージ
Write-Host ""
Write-Host "✅ キャッシュ削除が完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 アプリケーションを再起動するには:" -ForegroundColor Cyan
Write-Host "   .\run.ps1" -ForegroundColor White
Write-Host ""

