# 🎉 次のステップ：Streamlit Community Cloudにデプロイ

GitHubへのプッシュが完了したので、次はStreamlit Community Cloudにアプリをデプロイします。

## ✅ 現在の状態

- [x] コードがGitHubにプッシュ済み
- [x] `.gitignore`で`venv`が除外済み
- [x] `requirements.txt`が存在

## 🚀 デプロイ手順

### ステップ1: Streamlit Community Cloudにアクセス

1. ブラウザで以下にアクセス：
   - https://share.streamlit.io/

2. 「**Sign up**」または「**Log in**」をクリック

3. 「**Continue with GitHub**」をクリック

4. GitHubアカウントで認証（必要に応じて）

5. Streamlit Community Cloudへのアクセス権限を許可

### ステップ2: 新しいアプリを作成

1. ダッシュボード画面で「**New app**」ボタンをクリック

2. 以下の情報を入力：

   ```
   Repository: konnojp1995-hub/minpaku-project2  （ドロップダウンから選択）
   Branch: main                                   （通常はmain）
   Main file path: src/main.py                    （重要！）
   App URL: minpaku-chatbot                       （任意、URLの一部になります）
   ```

3. 「**Deploy!**」ボタンをクリック

### ステップ3: デプロイの待機

- ビルドログが表示されます
- 通常1〜3分程度かかります
- 「Your app is live!」と表示されたら完了

**デプロイが失敗した場合:**
- ビルドログを確認
- よくある問題：
  - `requirements.txt`に不足パッケージがある
  - `src/main.py`のパスが間違っている

### ステップ4: 環境変数（Secrets）の設定 ⚠️ 重要

デプロイが完了したら、APIキーを設定する必要があります。

1. アプリ画面の右上「**⋮**」（3つのドット）メニューをクリック

2. 「**Settings**」を選択

3. 左メニューから「**Secrets**」タブをクリック

4. 以下の形式でAPIキーを入力：

   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GEOCODING_API_KEY=your_geocoding_api_key_here
   ```

   **注意:**
   - `.env`ファイルと同じ形式
   - `=`の前後にスペースは入れない
   - 各変数は1行に1つ
   - 実際のAPIキーに置き換える

5. 「**Save**」をクリック（自動的に再デプロイされます）

### ステップ5: 動作確認

1. 「**Open app**」ボタンでアプリを開く

2. 以下の点を確認：
   - [ ] アプリが正常に読み込まれる
   - [ ] エラーメッセージが表示されない
   - [ ] サイドバーでAPIキー設定ができる
   - [ ] 基本的な機能が動作する

## 🔗 デプロイ後のURL

デプロイが完了すると、以下のようなURLが発行されます：

```
https://minpaku-chatbot.streamlit.app
```

このURLは永続的で、インターネットからアクセスできます！

## 📚 参考リンク

- [Streamlit Community Cloud ドキュメント](https://docs.streamlit.io/streamlit-community-cloud)
- [デプロイガイド](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Secrets管理](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

## 🔧 トラブルシューティング

### デプロイエラーが出る場合

**エラー: "Unable to locate package"（packages.txt関連）**
- `packages.txt`ファイルに日本語コメントや不要な内容がある可能性
- ファイルを空にするか、英語コメントのみに変更
- 変更後、コミット・プッシュして再デプロイ

**その他のエラー:**
詳細は [`DEPLOY_CHECKLIST.md`](./DEPLOY_CHECKLIST.md) のトラブルシューティングセクションを参照してください。
