# GitHub Personal Access Token 作成手順

GitHubにコードをプッシュする際に必要なPersonal Access Tokenの作成方法を説明します。

## 📝 手順（詳細版）

### ステップ1: GitHubにログイン

1. ブラウザで https://github.com にアクセス
2. 右上の「**Sign in**」をクリックしてログイン
   - ユーザー名: `konno1995-hub`
   - パスワードを入力

### ステップ2: Settings画面を開く

1. ログイン後、GitHubの右上にある**プロフィールアイコン**をクリック
   - 画面右上の丸いアイコン（アバター画像）
   - または、ユーザー名の横にある小さなアイコン

2. ドロップダウンメニューから「**Settings**」をクリック
   - Settingsは日本語表示の場合「設定」と表示されます

### ステップ3: Developer settingsに移動

Settings画面で、左側のメニューを下にスクロールします。

1. 左側メニューの一番下の方にある「**Developer settings**」をクリック
   - 日本語表示の場合「開発者向け設定」と表示されます
   - 画面の左側の縦に並んだメニューの下部にあります

### ステップ4: Personal access tokensに移動

Developer settings画面で：

1. 左側メニューから「**Personal access tokens**」をクリック
   - 日本語表示の場合「個人アクセストークン」と表示されます

2. さらにサブメニューが表示されるので、「**Tokens (classic)**」をクリック
   - または「**Fine-grained tokens**」でもOK（今回はclassicを推奨）

### ステップ5: 新しいトークンを生成

1. 「**Generate new token**」ボタンをクリック
   - 「Generate new token (classic)」と表示されているボタン

2. または「**Generate new token**」→「**Generate new token (classic)**」を選択

### ステップ6: トークンの設定

トークン作成画面で以下を設定：

1. **Note（メモ）**: 
   - トークンの用途を記入（例: `Streamlitデプロイ用` または `minpaku-chatbot`）

2. **Expiration（有効期限）**: 
   - ドロップダウンから選択
   - 推奨: 「**90 days**」または「**No expiration**」（無期限）

3. **Select scopes（スコープの選択）**: 
   - ⚠️ **重要**: 「**repo**」のチェックボックスを**必ずチェック**してください
   - 「repo」をチェックすると、以下のサブ項目も自動でチェックされます：
     - repo:status
     - repo_deployment
     - public_repo
     - repo:invite
     - security_events

4. 画面の下の方にスクロールして「**Generate token**」ボタンをクリック

### ステップ7: トークンをコピー

⚠️ **非常に重要**: この画面は**一度しか表示されません**！

1. 生成されたトークンが表示されます（長い文字列です）
   - 例: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **すぐにコピー**してください
   - トークンをクリックして選択し、`Ctrl+C`でコピー
   - または、右側にあるコピーボタン（📋アイコン）をクリック

3. **安全な場所に保存**してください（テキストファイル、パスワードマネージャーなど）
   - このページを離れると、もう一度確認できません
   - 失くした場合は、新しいトークンを生成する必要があります

## 🔐 トークンの使用

### プッシュ時の認証

GitHubにプッシュする際：

1. ユーザー名を求められたら: `konno1995-hub` を入力
2. パスワードを求められたら: **作成したトークン**を貼り付け
   - 通常のパスワードではなく、トークンを使用します

### 例: プッシュコマンド実行時

```powershell
git push -u origin main
```

実行すると：
```
Username for 'https://github.com': konno1995-hub
Password for 'https://konno1995-hub@github.com': [ここにトークンを貼り付け]
```

## 🔒 セキュリティに関する注意事項

1. **トークンは秘密にしてください**
   - パスワードと同じように扱ってください
   - GitHubにコミットしないでください
   - 他人と共有しないでください

2. **不要になったら削除**
   - Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 削除したいトークンの右側の「Delete」をクリック

3. **漏洩した場合は即座に削除**
   - トークンが漏洩した可能性がある場合は、すぐに削除して新しいトークンを生成

## 🔧 トラブルシューティング

### トークンが見つからない

- 一度ページを離れると表示されません
- 新しいトークンを生成してください
- 以前のトークンは使用できません（削除してから再生成）

### 認証エラーが出る

- トークンが正しくコピーされているか確認
- トークンの有効期限が切れていないか確認
- `repo`スコープが選択されているか確認

### トークンが表示されない

- ブラウザの拡張機能やポップアップブロッカーを確認
- 別のブラウザで試してみる

## 📚 参考リンク

- [GitHub公式ドキュメント: Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
