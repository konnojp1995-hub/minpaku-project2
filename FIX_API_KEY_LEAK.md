# Gemini APIキー漏洩エラーの解決方法

## 🔍 問題

エラーメッセージ：
```
403 Your API key was reported as leaked. Please use another API key.
```

これは、Gemini APIキーが漏洩したとGoogleに報告されているため、新しいAPIキーが必要です。

## ✅ 解決方法

### ステップ1: 新しいGemini APIキーを生成

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. ログイン（Googleアカウント）
3. 「**Create API Key**」または「**+ Create API Key**」をクリック
4. 新しいAPIキーが生成されます
5. **すぐにコピー**して安全な場所に保存

### ステップ2: Streamlit Community CloudのSecretsを更新

1. Streamlit Community Cloudのダッシュボードでアプリを開く
2. 「**⋮**」メニュー → 「**Settings**」を選択
3. 「**Secrets**」タブをクリック
4. 既存の`GEMINI_API_KEY`の値を**新しいAPIキー**に置き換え：

   ```
   GEMINI_API_KEY=新しいAPIキーをここに貼り付け
   ```

5. 「**Save**」をクリック（自動的に再デプロイされます）

### ステップ3: 古いAPIキーを無効化（推奨）

漏洩したAPIキーを無効化することを推奨します：

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 「APIs & Services」→「Credentials」を開く
3. 古いAPIキーを見つけて削除または無効化

## 🔒 セキュリティに関する注意事項

### APIキーが漏洩した原因の確認

以下を確認してください：

1. **コードに直接書かれていないか**
   - `src/`フォルダ内のファイルを確認
   - APIキーが直接書かれていないか確認

2. **`.env`ファイルがコミットされていないか**
   - `.gitignore`に`.env`が含まれているか確認（✅ 既に設定済み）
   - GitHubで`.env`ファイルが存在しないか確認

3. **GitHubのコミット履歴に含まれていないか**
   - 過去のコミットでAPIキーが含まれていないか確認

### 今後の対策

- ✅ APIキーは常に環境変数（Secrets）で管理
- ✅ `.env`ファイルは`.gitignore`に含める（✅ 既に設定済み）
- ✅ コードに直接APIキーを書かない
- ✅ 定期的にAPIキーをローテーション

## 🔄 アプリの再デプロイ

Secretsを更新すると、自動的に再デプロイが開始されます。数分待ってから、アプリが正常に動作するか確認してください。
