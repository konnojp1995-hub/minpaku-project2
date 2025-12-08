# venvフォルダのエラー解決方法

## 🔍 問題の原因

`venv`フォルダ（仮想環境）がコミットされており、GitHubの100MB制限を超えています。

エラー内容：
- `torch_cpu.dll` (245.80 MB) - GitHubの100MB制限を超過
- `cv2.pyd` (67.68 MB) - 推奨上限50MBを超過

## ✅ 解決方法

### ステップ1: venvフォルダをGitの追跡から削除

```powershell
# venvフォルダをGitのインデックスから削除（ファイル自体は削除されません）
git rm -r --cached venv/

# .gitignoreが正しく設定されているか確認（venv/が含まれていることを確認）
```

### ステップ2: 変更をコミット

```powershell
# 変更をステージング
git add .gitignore

# コミット
git commit -m "Remove venv folder from Git tracking"
```

### ステップ3: GitHubにプッシュ

```powershell
git push -u origin main
```

## 🔧 もしまだエラーが出る場合

既に`venv`がコミット履歴に含まれている場合、履歴を書き換える必要があります：

```powershell
# 最後のコミットからvenvを削除
git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch venv" --prune-empty --tag-name-filter cat -- --all

# または、より簡単な方法（git-filter-repoを使用する場合）
# ただし、これは新しいコマンドなので、まずは上の方法を試してください
```

## 📝 重要な注意事項

⚠️ **重要**: `venv`フォルダは**絶対にコミットしないでください**。

理由：
- サイズが非常に大きい（数百MB）
- 環境依存のファイルが含まれる
- 他の開発者の環境では動作しない
- `.gitignore`で除外すべき

`.gitignore`に`venv/`が含まれていることを確認してください（既に含まれています）。
