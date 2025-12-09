# 「This repository does not exist」エラーの解決方法

## 🔍 原因の確認

このエラーが出る主な原因は以下です：

1. **リポジトリ名またはユーザー名が間違っている**
2. **リポジトリが存在しない**
3. **リポジトリがプライベートで、Streamlit Community Cloudへのアクセス権限がない**

## ✅ 確認手順

### ステップ1: GitHubでリポジトリの存在を確認

ブラウザで以下にアクセスしてください：

- https://github.com/konnojp1995-hub/minpaku-project2

**結果:**
- ✅ リポジトリが表示される → ステップ2へ
- ❌ 404エラーが出る → リポジトリが存在しません。作成してください。

### ステップ2: リポジトリのURLを確認

リポジトリページの上部に表示されるURLを確認してください。

正しい形式：
```
https://github.com/USERNAME/REPOSITORY-NAME
```

### ステップ3: リポジトリがパブリックかプライベートか確認

- **Public（公開）**: Streamlit Community Cloudで直接デプロイ可能
- **Private（非公開）**: Streamlit Community Cloudへのアクセス権限が必要

## 🔧 解決方法

### 解決方法1: リポジトリが存在しない場合

リポジトリが存在しない場合は、作成してください：

1. https://github.com/new にアクセス
2. Repository name: `minpaku-project2` を入力
3. PublicまたはPrivateを選択
4. 「Create repository」をクリック
5. コードをプッシュ（既にプッシュ済みの場合はスキップ）

### 解決方法2: ユーザー名が間違っている場合

ターミナルで以下を実行して、正しいリモートURLを確認：

```powershell
git remote -v
```

表示されたURLのユーザー名と、GitHubでログインしているユーザー名が一致しているか確認してください。

### 解決方法3: プライベートリポジトリの場合

Streamlit Community Cloudでプライベートリポジトリを使用する場合：

1. Streamlit Community Cloudのダッシュボードで「Settings」を開く
2. 「Repositories」セクションで、リポジトリへのアクセス権限を許可
3. または、リポジトリをパブリックに変更

### 解決方法4: リポジトリ名を正確に入力

Streamlit Community Cloudのデプロイ画面で：

- 「Paste GitHub URL」ではなく、**「Repository」ドロップダウン**から選択する方法を試してください
- または、完全なURL形式で入力：
  ```
  https://github.com/konnojp1995-hub/minpaku-project2
  ```

## 🔍 よくある問題

### 問題: ユーザー名の不一致

ターミナルのログでは `konnojp1995-hub` となっていますが、実際のGitHubユーザー名が異なる可能性があります。

**確認方法:**
1. GitHubにログイン
2. 右上のプロフィールアイコンをクリック
3. ユーザー名を確認

### 問題: リポジトリが表示されない

Streamlit Community Cloudのリポジトリ一覧に表示されない場合：

1. GitHubでリポジトリが存在することを確認
2. Streamlit Community Cloudへのアクセス権限を再承認
3. リポジトリを一度削除して再作成（最後の手段）

## ✅ チェックリスト

- [ ] GitHubでリポジトリが存在することを確認
- [ ] リポジトリURLが正しいことを確認
- [ ] ユーザー名が正しいことを確認
- [ ] リポジトリがパブリックか、プライベートの場合はアクセス権限があるか確認
- [ ] Streamlit Community CloudにGitHubアカウントが正しく連携されているか確認
