# キャッシュ削除と再実行手順

Streamlitアプリケーションのキャッシュを削除して再実行する手順を説明します。

## 📋 目次

1. [キャッシュの種類](#キャッシュの種類)
2. [キャッシュ削除手順](#キャッシュ削除手順)
3. [再実行手順](#再実行手順)
4. [トラブルシューティング](#トラブルシューティング)

## 🗂️ キャッシュの種類

Streamlitアプリケーションでは、以下のキャッシュが使用されます：

### 1. Streamlitのキャッシュ
- 場所: `%USERPROFILE%\.streamlit\cache\` (Windows)
- 内容: `@st.cache_data` や `@st.cache_resource` でキャッシュされたデータ

### 2. Pythonのコンパイルキャッシュ（`__pycache__`）
- 場所: `src/` と `src/modules/` 内
- 内容: Pythonのバイトコード（`.pyc` ファイル）

### 3. Streamlitのセッション状態
- 場所: メモリ内（ブラウザのセッション）
- 内容: アプリケーションの状態情報

## 🧹 キャッシュ削除手順

### 方法1: 自動スクリプトを使用（推奨）

**Windows（PowerShell）**
```powershell
.\clear_cache.ps1
```

**Windows（コマンドプロンプト）**
```cmd
clear_cache.bat
```

### 方法2: 手動で削除

#### Step 1: Streamlitアプリケーションを停止

ブラウザで `Ctrl+C` を押すか、コマンドプロンプトで実行中のプロセスを停止します。

#### Step 2: Streamlitのキャッシュを削除

**PowerShell**
```powershell
# Streamlitのキャッシュディレクトリを削除
Remove-Item -Path "$env:USERPROFILE\.streamlit\cache" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Streamlitのキャッシュを削除しました"
```

**コマンドプロンプト**
```cmd
rd /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
echo ✅ Streamlitのキャッシュを削除しました
```

#### Step 3: Pythonのコンパイルキャッシュを削除

**PowerShell**
```powershell
# プロジェクト内の __pycache__ ディレクトリを削除
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
Write-Host "✅ Pythonのコンパイルキャッシュを削除しました"
```

**コマンドプロンプト**
```cmd
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
echo ✅ Pythonのコンパイルキャッシュを削除しました
```

#### Step 4: 一時ファイルを削除（オプション）

プロジェクト内の一時ファイルも削除できます：

**PowerShell**
```powershell
# temp_ で始まるファイルを削除
Get-ChildItem -Path . -Filter "temp_*" -File -Recurse | Remove-Item -Force
Write-Host "✅ 一時ファイルを削除しました"
```

**コマンドプロンプト**
```cmd
del /s /q temp_* 2>nul
echo ✅ 一時ファイルを削除しました
```

## 🚀 再実行手順

キャッシュを削除した後、以下の手順でアプリケーションを再起動してください。

### 方法1: 起動スクリプトを使用（推奨）

**Windows（PowerShell）**
```powershell
.\run.ps1
```

**Windows（コマンドプロンプト）**
```cmd
run.bat
```

### 方法2: 手動で起動

**Windows（PowerShell）**
```powershell
# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# Streamlitアプリを起動
streamlit run src/main.py
```

**Windows（コマンドプロンプト）**
```cmd
# 仮想環境を有効化
venv\Scripts\activate.bat

# Streamlitアプリを起動
streamlit run src/main.py
```

## 🔧 トラブルシューティング

### キャッシュが削除できない場合

#### 1. アプリケーションが実行中
- **解決策**: まずアプリケーションを完全に停止してください
- タスクマネージャーで `streamlit.exe` や `python.exe` プロセスを確認し、終了してください

#### 2. ファイルがロックされている
- **解決策**: すべてのStreamlitブラウザータブを閉じてから再試行してください

#### 3. 権限の問題
- **解決策**: 管理者権限でPowerShellやコマンドプロンプトを実行してください

### キャッシュ削除後も問題が解決しない場合

#### 1. ブラウザのキャッシュをクリア
- **Chrome/Edge**: `Ctrl+Shift+Delete` → キャッシュされた画像とファイルを選択 → 削除
- **Firefox**: `Ctrl+Shift+Delete` → キャッシュを選択 → 削除

#### 2. セッション状態をリセット
- ブラウザで `Ctrl+F5` を押してページを強制リロード
- または、ブラウザの開発者ツール（F12）で Application → Storage → Clear site data

#### 3. 仮想環境を再作成（最後の手段）
```powershell
# 仮想環境を削除
Remove-Item -Path .\venv -Recurse -Force

# 仮想環境を再作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 依存関係を再インストール
pip install -r requirements.txt
```

## 📝 注意事項

- キャッシュを削除すると、アプリケーションの起動が初回起動時と同じように少し遅くなる可能性があります（これは正常です）
- `@st.cache_data` でキャッシュされたデータは次回の実行時に再計算されます
- セッション状態（`st.session_state`）はブラウザ内に保存されるため、キャッシュ削除では影響を受けません

## 🔄 クイックリセットコマンド（まとめて実行）

**PowerShell（一括実行）**
```powershell
# アプリケーションを停止（実行中の場合は手動で停止）
Write-Host "🛑 アプリケーションを停止してください（Ctrl+C）"

# キャッシュを削除
Write-Host "🧹 キャッシュを削除中..."
Remove-Item -Path "$env:USERPROFILE\.streamlit\cache" -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "temp_*" -File -Recurse | Remove-Item -Force

Write-Host "✅ キャッシュを削除しました"
Write-Host "🚀 アプリケーションを再起動してください"
```

**コマンドプロンプト（一括実行）**
```cmd
@echo off
echo 🛑 アプリケーションを停止してください（Ctrl+C）
pause

echo 🧹 キャッシュを削除中...
rd /s /q "%USERPROFILE%\.streamlit\cache" 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q temp_* 2>nul

echo ✅ キャッシュを削除しました
echo 🚀 アプリケーションを再起動してください
```

