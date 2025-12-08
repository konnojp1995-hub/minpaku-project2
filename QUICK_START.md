# クイックスタートガイド

## 初回セットアップ（1回だけ実行）

```bash
# 1. 依存関係のインストール
pip install -r requirements.txt
```

## 毎回の起動方法

### 🚀 簡単な方法（推奨）

**PowerShellの場合：**
```powershell
.\run.ps1
```

**コマンドプロンプトの場合：**
```cmd
run.bat
```

これだけです！仮想環境が自動で有効化され、アプリが起動します。

---

### 📝 手動で起動する場合

**PowerShell:**
```powershell
# 1. 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 2. アプリを起動
streamlit run src/main.py
```

**コマンドプロンプト:**
```cmd
rem 1. 仮想環境を有効化
venv\Scripts\activate.bat

rem 2. アプリを起動
streamlit run src/main.py
```

---

## 確認方法

仮想環境が有効化されていると、プロンプトの前に `(venv)` が表示されます：
```
(venv) PS C:\Users\konno\Projects\minpaku-chatbot>
```

この状態で実行すれば、すべてのライブラリが正しく認識されます。

---

## アプリの停止

アプリを停止する場合は、ターミナルで `Ctrl + C` を押してください。

---

## トラブルシューティング

### PowerShellスクリプトが実行できない

以下のコマンドを実行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ライブラリが見つからないエラー

仮想環境が有効化されていることを確認してください。
プロンプトに `(venv)` が表示されていない場合は、上記の手順で仮想環境を有効化してください。

