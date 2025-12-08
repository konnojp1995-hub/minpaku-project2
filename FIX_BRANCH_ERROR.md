# 「This branch does not exist」エラーの解決方法

Streamlit Community Cloudで「This branch does not exist」と表示される場合の対処法です。

## 🔍 原因

指定したブランチ（通常は`main`または`master`）がGitHubリポジトリに存在しないことを意味します。

## ✅ 解決手順

### ステップ1: 現在のブランチ名を確認

プロジェクトフォルダで以下を実行して、現在のブランチ名を確認します：

**PowerShellまたはコマンドプロンプト:**
```bash
git branch
```

現在のブランチ名が表示されます（例：`* main` や `* master`）。

### ステップ2: GitHubにコードをプッシュ

まだコードをプッシュしていない場合、以下の手順でプッシュします：

```bash
# 1. 現在のブランチを確認（ステップ1で確認済み）
git branch

# 2. すべてのファイルをステージング（.envファイルは除外されることを確認）
git add .

# 3. コミット（まだコミットしていない場合）
git commit -m "Initial commit: Minpaku chatbot app"

# 4. リモートリポジトリを確認（既に設定済みの場合）
git remote -v

# 5. リモートリポジトリが設定されていない場合、追加
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 6. 現在のブランチをGitHubにプッシュ
git push -u origin main
# または、ブランチ名がmasterの場合
git push -u origin master
```

### ステップ3: GitHubでブランチ名を確認

1. GitHubリポジトリ（`https://github.com/YOUR_USERNAME/YOUR_REPO`）にアクセス
2. リポジトリの上部に表示されるブランチ名を確認（通常は`main`または`master`）
3. 「branch: main」などの表示を確認

### ステップ4: Streamlit Community Cloudで正しいブランチを指定

Streamlit Community Cloudのデプロイ画面で：

1. **Repository**を選択
2. **Branch**のドロップダウンから、GitHubで確認したブランチ名を選択
   - GitHubで`main`が表示されている場合 → `main`を選択
   - GitHubで`master`が表示されている場合 → `master`を選択
3. **Main file path**: `src/main.py`を入力
4. 「Deploy!」をクリック

## 🔄 ブランチ名を変更したい場合

### mainに統一したい場合

```bash
# 現在masterブランチにいる場合
git branch -M main
git push -u origin main
```

### masterに統一したい場合

```bash
# 現在mainブランチにいる場合
git branch -M master
git push -u origin master
```

## ❓ よくある質問

### Q: リポジトリは作成したけど、コードをまだプッシュしていない

**A:** 上記のステップ2を実行してコードをプッシュしてください。

### Q: どのブランチが存在するかわからない

**A:** 以下で確認できます：
```bash
# ローカルのブランチを確認
git branch

# リモートのブランチを確認
git branch -r

# GitHubリポジトリのページで確認
# https://github.com/YOUR_USERNAME/YOUR_REPO/branches
```

### Q: 「remote origin already exists」と表示される

**A:** 既にリモートリポジトリが設定されています。以下のコマンドで確認：
```bash
git remote -v
```

別のリポジトリを設定したい場合：
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### Q: プッシュ時に認証エラーが出る

**A:** GitHubの認証が必要です。以下のいずれかの方法を使用：

1. **Personal Access Tokenを使用:**
   - GitHub → Settings → Developer settings → Personal access tokens → Generate new token
   - パスワードの代わりにトークンを使用

2. **GitHub CLIを使用:**
   ```bash
   gh auth login
   ```

## 📝 チェックリスト

デプロイ前に以下を確認：

- [ ] コードがGitHubリポジトリにプッシュされている
- [ ] GitHubリポジトリのページでブランチ名を確認済み
- [ ] Streamlit Community Cloudで正しいブランチ名を選択している
- [ ] `src/main.py`のパスが正しい
- [ ] `requirements.txt`がプロジェクトルートにある

## 🔗 関連リンク

- [Gitブランチ管理の基礎](https://git-scm.com/book/ja/v2/Git-%E3%81%AE%E3%83%96%E3%83%A9%E3%83%B3%E3%83%81%E6%A9%9F%E8%83%BD)
- [GitHubでのブランチ確認方法](https://docs.github.com/ja/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository)
