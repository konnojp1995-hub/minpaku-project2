# Streamlit Community Cloud デプロイチェックリスト

GitHubリポジトリを作成した後の、Streamlit Community Cloudへのデプロイ手順を確認します。

## ✅ デプロイ前の確認事項

### 1. GitHubリポジトリの準備

- [ ] コードがGitHubにプッシュされている
- [ ] `.gitignore`に`.env`が含まれている（APIキーが公開されないように）
- [ ] `requirements.txt`がプロジェクトルートにある
- [ ] `src/main.py`が存在する

### 2. 必要なファイルの確認

プロジェクトルートに以下があることを確認：

```
minpaku-chatbot/
├── requirements.txt          ✅ 必要
├── src/
│   └── main.py              ✅ 必要
├── .gitignore               ✅ 推奨（.envが含まれていること）
└── data/                    ✅ 必要（用途地域データなど）
```

## 🚀 デプロイ手順（リポジトリ作成後）

### ステップ1: Streamlit Community Cloudにサインアップ/ログイン

1. [https://share.streamlit.io/](https://share.streamlit.io/) にアクセス
2. 「Sign up」または「Log in」をクリック
3. 「Continue with GitHub」でGitHubアカウントと連携
4. Streamlit Community Cloudへのアクセス権限を許可

### ステップ2: 新しいアプリを作成

1. ダッシュボードで「**New app**」ボタンをクリック
2. 以下の情報を入力：

```
Repository: YOUR_USERNAME/YOUR_REPO_NAME  （ドロップダウンから選択）
Branch: main                              （通常はmain）
Main file path: src/main.py               （重要！）
App URL: minpaku-chatbot                  （任意、URLの一部になります）
```

3. 「**Deploy!**」ボタンをクリック

### ステップ3: デプロイの待機

- ビルドログが表示されます
- 通常1〜3分程度かかります
- 「Your app is live!」と表示されたら完了

### ステップ4: 環境変数（Secrets）の設定

1. アプリ画面の右上「**⋮**」メニューをクリック
2. 「**Settings**」を選択
3. 左メニューから「**Secrets**」タブをクリック
4. 以下の形式でAPIキーを入力：

```
GOOGLE_MAPS_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GEOCODING_API_KEY=your_key_here
```

5. 「**Save**」をクリック（自動的に再デプロイされます）

### ステップ5: 動作確認

1. 「**Open app**」ボタンでアプリを開く
2. 以下の点を確認：
   - [ ] アプリが正常に読み込まれる
   - [ ] エラーメッセージが表示されない
   - [ ] サイドバーでAPIキー設定ができる
   - [ ] 基本的な機能が動作する

## 🔧 トラブルシューティング

### デプロイが失敗する場合

**エラー: "Module not found"**
- `requirements.txt`に不足しているパッケージがある可能性
- ビルドログを確認して、どのパッケージが不足しているか確認
- `requirements.txt`に追加して、再度コミット・プッシュ

**エラー: "File not found: src/main.py"**
- `Main file path`が正しいか確認（`src/main.py`であること）
- GitHubリポジトリでファイルパスが正しいか確認

**エラー: "Import error"**
- ローカルで動作することを確認
- 仮想環境でテスト: `streamlit run src/main.py`

### Secretsが反映されない場合

1. 「Settings」→「Secrets」で正しく保存されているか確認
2. アプリの「⋮」メニューから「**Redeploy**」を選択して手動再デプロイ
3. 数分待ってから再度アクセス

### パッケージのインストールエラー

`requirements.txt`に問題がある可能性があります。以下を確認：

1. すべての依存パッケージが含まれているか
2. バージョン指定が正しいか
3. Streamlit Community Cloudでサポートされていないパッケージがないか

よく問題になるパッケージ：
- `tesseract` / `pytesseract` - システムパッケージが必要な場合がある
- 大きなバイナリファイルを含むパッケージ

## 📝 デプロイ後の確認

- [ ] アプリのURLを確認（例: `https://minpaku-chatbot.streamlit.app`）
- [ ] インターネットからアクセスできることを確認
- [ ] APIキーが正しく読み込まれていることを確認
- [ ] 基本的な機能をテスト

## 🔄 更新方法

コードを更新した場合：

1. ローカルで変更をコミット
2. GitHubにプッシュ: `git push origin main`
3. Streamlit Community Cloudが自動的に再デプロイします
4. 数分待ってアプリをリロード

## 📚 参考リンク

- [Streamlit Community Cloud ドキュメント](https://docs.streamlit.io/streamlit-community-cloud)
- [デプロイガイド](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Secrets管理](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
