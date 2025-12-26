# 永続的なデプロイガイド

このアプリケーションをインターネットに永続的に公開する方法を説明します。

## 🚀 推奨方法：Streamlit Community Cloud（最も簡単）

### 前提条件
- GitHubアカウント
- GitHubリポジトリにコードがプッシュされていること

### デプロイ手順

#### 1. Streamlit Community Cloudにアクセス
1. [Streamlit Community Cloud](https://share.streamlit.io/) にアクセス
2. 「Sign up」または「Log in」をクリック
3. GitHubアカウントでログイン

#### 2. 新しいアプリを作成
1. ダッシュボードで「New app」をクリック
2. 以下の設定を入力：
   - **Repository**: `konnojp1995-hub/minpaku-project2` を選択
   - **Branch**: `main` を選択
   - **Main file path**: `src/main.py` を入力
   - **App URL**（オプション）: カスタムURLを設定（例: `minpaku-chatbot`）
3. 「Deploy!」をクリック

#### 3. 環境変数（Secrets）の設定
デプロイ後、APIキーを設定する必要があります：

1. アプリのダッシュボードで「⋮」（3つのドット）メニューをクリック
2. 「Settings」を選択
3. 「Secrets」タブをクリック
4. 以下の形式で環境変数を入力：

```toml
GOOGLE_MAPS_API_KEY = "your_google_maps_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
GEOCODING_API_KEY = "your_geocoding_api_key_here"
MAX_FILE_SIZE_MB = 10
```

5. 「Save」をクリック（自動的に再デプロイされます）

#### 4. アクセス
デプロイが完了すると、以下のようなURLが発行されます：
```
https://[アプリ名].streamlit.app
```

このURLは永続的で、インターネット上のどこからでもアクセスできます。

---

## 🔧 代替方法1：Railway（柔軟な選択肢）

### 前提条件
- GitHubアカウント
- [Railway](https://railway.app/) アカウント（無料プランあり）

### デプロイ手順

#### 1. Railwayにサインアップ
1. [Railway](https://railway.app/) にアクセス
2. GitHubアカウントでサインアップ

#### 2. 新しいプロジェクトを作成
1. 「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. `konnojp1995-hub/minpaku-project2` を選択

#### 3. 設定の確認
Railwayは自動的に以下を検出します：
- **Pythonアプリケーション**として認識
- `requirements.txt` から依存関係をインストール

#### 4. 起動コマンドの設定
「Settings」タブで、以下の起動コマンドを設定：
```
streamlit run src/main.py --server.port=$PORT --server.address=0.0.0.0
```

#### 5. 環境変数の設定
「Variables」タブで以下の環境変数を設定：
- `GOOGLE_MAPS_API_KEY`: Google Maps APIキー
- `GEMINI_API_KEY`: Gemini APIキー
- `GEOCODING_API_KEY`: Geocoding APIキー
- `MAX_FILE_SIZE_MB`: 10

#### 6. デプロイ
自動的にデプロイが開始されます。完了すると、RailwayからURLが発行されます。

---

## 🌐 代替方法2：Render（シンプル）

### 前提条件
- GitHubアカウント
- [Render](https://render.com/) アカウント（無料プランあり）

### デプロイ手順

#### 1. Renderにサインアップ
1. [Render](https://render.com/) にアクセス
2. GitHubアカウントでサインアップ

#### 2. 新しいWebサービスを作成
1. 「New +」→「Web Service」をクリック
2. GitHubリポジトリ `konnojp1995-hub/minpaku-project2` を接続

#### 3. 設定
- **Name**: アプリ名（例: `minpaku-chatbot`）
- **Region**: 最寄りのリージョンを選択
- **Branch**: `main`
- **Root Directory**: （空欄のまま）
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run src/main.py --server.port=$PORT --server.address=0.0.0.0`

#### 4. 環境変数の設定
「Environment」セクションで以下を設定：
- `GOOGLE_MAPS_API_KEY`: Google Maps APIキー
- `GEMINI_API_KEY`: Gemini APIキー
- `GEOCODING_API_KEY`: Geocoding APIキー
- `MAX_FILE_SIZE_MB`: 10

#### 5. デプロイ
「Create Web Service」をクリックしてデプロイを開始します。

---

## 📋 デプロイ前のチェックリスト

- [ ] `requirements.txt` が最新である
- [ ] `.env` ファイルが `.gitignore` に含まれている（APIキーがコミットされていない）
- [ ] GitHubにコードがプッシュされている
- [ ] 必要なAPIキーを準備している

---

## 🔒 セキュリティに関する注意事項

1. **APIキーの保護**:
   - `.env` ファイルは絶対にコミットしない
   - デプロイ先のSecrets/環境変数機能を使用する
   - 公開リポジトリの場合は特に注意

2. **アクセス制限**（オプション）:
   - Streamlit Community Cloudでは認証機能が利用可能
   - 機密情報を扱う場合は認証を検討

---

## 🐛 トラブルシューティング

### デプロイが失敗する場合

1. **ビルドログを確認**:
   - デプロイ先のダッシュボードでビルドログを確認
   - エラーメッセージを確認

2. **よくある問題**:
   - `requirements.txt` に必要なパッケージが不足
   - パスの指定が間違っている（`src/main.py` が正しい）
   - 環境変数が設定されていない

3. **依存関係の問題**:
   - GeoPandasなどの地理空間ライブラリは時間がかかることがある
   - ビルドタイムアウトに注意

### アプリが起動しない場合

1. **ログを確認**:
   - デプロイ先のダッシュボードでログを確認
   - エラーメッセージを確認

2. **環境変数の確認**:
   - すべての環境変数が正しく設定されているか確認
   - 値に余分なスペースや引用符が含まれていないか確認

---

## 📚 参考リンク

- [Streamlit Community Cloud ドキュメント](https://docs.streamlit.io/streamlit-community-cloud)
- [Railway ドキュメント](https://docs.railway.app/)
- [Render ドキュメント](https://render.com/docs)

