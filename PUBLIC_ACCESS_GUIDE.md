# インターネットからアクセスする方法

このアプリケーションをインターネットからアクセスできるようにする方法を説明します。

## 方法1: ngrokを使用（推奨：簡単で高速）

ngrokを使用すると、ローカルで実行しているアプリを一時的にインターネットに公開できます。

### セットアップ手順

#### 1. ngrokのインストール

1. [ngrok公式サイト](https://ngrok.com/download)からngrokをダウンロード
2. ダウンロードしたzipファイルを解凍
3. 以下のいずれかを行う：
   - `ngrok.exe`をこのプロジェクトフォルダに配置
   - または、ngrokをシステムのPATHに追加

#### 2. ngrokアカウントの作成と認証

1. [ngrok無料アカウント](https://dashboard.ngrok.com/signup)を作成
2. ダッシュボードで「Your Authtoken」を確認
3. コマンドプロンプトまたはPowerShellで以下を実行：

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

#### 3. アプリの起動

**PowerShellの場合:**
```powershell
.\run_public.ps1
```

**コマンドプロンプトの場合:**
```cmd
run_public.bat
```

スクリプトが以下を自動で行います：
- Streamlitアプリを起動（`localhost:8501`でリッスン）
- ngrokトンネルを作成
- パブリックURLを表示

#### 4. パブリックURLの確認

スクリプト実行後、以下のようなURLが表示されます：

```
https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

このURLをインターネット上からアクセスできます。

また、ngrokのダッシュボードで詳細を確認できます：
- http://localhost:4040

### 注意事項

- **無料プランの制限:**
  - URLは起動のたびに変わります
  - セッション時間の制限があります（再起動が必要になる場合があります）
  - 同時接続数に制限があります

- **セキュリティ:**
  - この方法で公開したアプリは、URLを知っている誰でもアクセスできます
  - 機密情報を扱う場合は注意してください

## 方法2: Streamlit Community Cloudにデプロイ（推奨：永続的）

Streamlit Community Cloudを使用すると、無料でアプリを永続的にホスティングできます。

### セットアップ手順

#### 1. GitHubリポジトリの準備

**⚠️ 重要：GitHubリポジトリを既に作成している場合、このステップはスキップしてください。**

アプリケーションをGitHubにプッシュする必要があります。

```bash
# プロジェクトフォルダで実行

# Gitリポジトリを初期化（まだの場合）
git init

# .gitignoreが存在することを確認（.envファイルなどが含まれているか確認）
# .envファイルをコミットしないように注意！

# すべてのファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit: Minpaku chatbot app"

# GitHubリポジトリをリモートとして追加
# YOUR_USERNAME と YOUR_REPO を実際の値に置き換えてください
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# メインブランチにプッシュ
git branch -M main
git push -u origin main
```

**既にリポジトリを作成してコードをプッシュ済みの場合は、次のステップに進んでください。**

#### 2. 必要なファイルの確認

デプロイ前に、以下がプロジェクトルートにあることを確認してください：

- ✅ `requirements.txt` - Python依存パッケージのリスト（既に存在します）
- ✅ `src/main.py` - Streamlitアプリのメインファイル（既に存在します）
- ✅ `.gitignore` - `.env`ファイルがコミットされないように設定されていることを確認

#### 3. Streamlit Community Cloudにデプロイ

##### ステップ1: Streamlit Community Cloudにアクセス

1. ブラウザで [Streamlit Community Cloud](https://share.streamlit.io/) にアクセス
2. 「Sign up」ボタン（初回の場合）または「Log in」ボタンをクリック

##### ステップ2: GitHubアカウントでログイン

1. 「Continue with GitHub」をクリック
2. GitHubの認証画面が表示されるので、認証を完了
3. Streamlit Community Cloudへのアクセス権限を許可

##### ステップ3: 新しいアプリを作成

1. ログイン後、ダッシュボード画面が表示されます
2. 右上の「New app」ボタンをクリック

##### ステップ4: デプロイ設定

「Create a new app」画面で以下を設定：

1. **Repository（リポジトリ）**: 
   - ドロップダウンからあなたのGitHubリポジトリ（`YOUR_USERNAME/YOUR_REPO`）を選択
   - 表示されない場合は、リポジトリ名を検索して選択

2. **Branch（ブランチ）**: 
   - `main` または `master` を選択（通常は `main`）

3. **Main file path（メインファイルパス）**: 
   - **重要**: `src/main.py` と入力（プロジェクトルートからの相対パス）

4. **App URL（アプリURL）**（オプション）:
   - 自動生成されるURLを使用するか、カスタムURLを設定できます
   - 例: `minpaku-chatbot` → `https://minpaku-chatbot.streamlit.app`

5. 「Deploy!」ボタンをクリック

##### ステップ5: デプロイの待機

- デプロイが開始されると、ビルドログが表示されます
- 通常、1〜3分程度かかります
- 初回デプロイは依存パッケージのインストールで時間がかかる場合があります

**デプロイが失敗した場合:**
- ビルドログを確認してエラーメッセージを確認
- よくある問題：
  - `requirements.txt`に必要なパッケージが不足している
  - `src/main.py`のパスが間違っている
  - インポートエラー

#### 4. 環境変数（Secrets）の設定

デプロイが完了したら、APIキーなどの機密情報を設定する必要があります。

##### ステップ1: Settings画面を開く

1. アプリのダッシュボード画面で、右上の「⋮」（3つのドット）メニューをクリック
2. 「Settings」を選択

##### ステップ2: Secretsを設定

1. 左側のメニューから「Secrets」タブをクリック
2. 「Secrets」テキストエリアに、以下の形式で環境変数を入力：

```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEOCODING_API_KEY=your_geocoding_api_key_here
```

**注意事項:**
- `.env`ファイルと同じ形式で記述してください
- `=`の前後にスペースは入れないでください
- 各変数は1行に1つずつ記述してください
- APIキーは実際の値に置き換えてください

3. 「Save」ボタンをクリック

##### ステップ3: アプリの再デプロイ

Secretsを保存すると、アプリが自動的に再デプロイされます（通常は数十秒）。

**Secretsが反映されない場合:**
- アプリの「⋮」メニューから「Redeploy」を選択して手動で再デプロイ

#### 5. アクセスと確認

デプロイが完了すると、以下のようなURLが発行されます：

```
https://YOUR_APP_NAME.streamlit.app
```

**アクセス方法:**
1. アプリのダッシュボード画面で「Open app」ボタンをクリック
2. または、URLをブラウザで直接開く

このURLは永続的で、インターネット上のどこからでもアクセスできます。

**動作確認:**
- アプリが正常に読み込まれるか確認
- サイドバーの設定でAPIキーが正しく読み込まれているか確認
- 基本的な機能が動作するかテスト

### 注意事項

- **ファイルサイズ制限:**
  - アップロードできるファイルサイズに制限があります
  - 大きなデータファイルは外部ストレージを使用することを検討してください

- **実行時間制限:**
  - 無料プランでは実行時間に制限があります

- **プライベートリポジトリ:**
  - Streamlit Community Cloudは無料プランでプライベートリポジトリもサポートしています

## 方法3: その他のクラウドプラットフォーム

以下のプラットフォームでもデプロイ可能です：

### Heroku

```bash
# Heroku CLIをインストール後
heroku create your-app-name
git push heroku main
```

### Railway

1. [Railway](https://railway.app/)にサインアップ
2. 新しいプロジェクトを作成
3. GitHubリポジトリを接続
4. 自動デプロイが開始されます

### Render

1. [Render](https://render.com/)にサインアップ
2. 新しいWebサービスを作成
3. GitHubリポジトリを接続
4. ビルドコマンドと起動コマンドを設定：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run src/main.py --server.port=$PORT --server.address=0.0.0.0`

## トラブルシューティング

### ngrokで接続できない場合

1. **ファイアウォールの確認:**
   - Windowsファイアウォールでポート8501を許可してください

2. **ngrok認証エラー:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

3. **ポートが使用中:**
   - 別のアプリケーションがポート8501を使用していないか確認
   - Streamlitのポートを変更: `streamlit run src/main.py --server.port=8502`
   - ngrokも対応するポートに変更: `ngrok http 8502`

### Streamlit Community Cloudでデプロイエラー

1. **依存関係の確認:**
   - `requirements.txt`にすべての依存関係が含まれているか確認

2. **ログの確認:**
   - Streamlit Community Cloudのダッシュボードでログを確認

3. **環境変数の確認:**
   - Secretsに正しく設定されているか確認

## セキュリティに関する推奨事項

1. **APIキーの保護:**
   - APIキーは環境変数として管理し、コードに直接記述しない
   - GitHubにプッシュする前に`.env`ファイルが`.gitignore`に含まれているか確認

2. **アクセス制限:**
   - 可能であれば、認証機能を追加することを検討
   - 機密情報を扱う場合は、適切なアクセス制御を実装

3. **HTTPSの使用:**
   - Streamlit Community Cloudは自動でHTTPSを提供
   - ngrokも無料プランでHTTPSを使用可能

## 参考リンク

- [ngrok公式ドキュメント](https://ngrok.com/docs)
- [Streamlit Community Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit設定オプション](https://docs.streamlit.io/library/advanced-features/configuration)
