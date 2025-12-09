# packages.txtをGitHubから削除する方法

## 🔧 方法1: GitHubのWebインターフェースから削除（推奨・最も確実）

### ステップ1: ファイルページを開く

1. ブラウザで以下にアクセス：
   - https://github.com/konnojp1995-hub/minpaku-project2/blob/main/packages.txt

### ステップ2: ファイルを削除

1. ファイル表示画面の右上にある「**🗑️ Delete file**」ボタンをクリック
   - または「**Delete**」ボタン

2. 確認画面が表示されます：
   - コミットメッセージを入力（例: `Remove packages.txt`）
   - 「**Commit changes**」ボタンをクリック

3. これでファイルが削除され、自動的にコミット・プッシュされます

## 🔧 方法2: ローカルから確実にプッシュ

もし方法1が使えない場合：

```powershell
# 現在の状態を確認
git status

# packages.txtが存在する場合、削除
git rm packages.txt

# 変更をコミット
git commit -m "Remove packages.txt"

# プッシュ
git push origin main

# 確認：リモートの状態を確認
git ls-remote origin main
```

## ✅ 確認方法

削除後、以下にアクセスしてファイルが存在しないことを確認：

- https://github.com/konnojp1995-hub/minpaku-project2/tree/main

`packages.txt`が表示されていなければ成功です。

## 🎯 削除後の動作

`packages.txt`が存在しない場合、Streamlit Community Cloudは：
- システムパッケージのインストールをスキップ
- Pythonパッケージのインストールに直接進みます

これでエラーが解消されるはずです。
