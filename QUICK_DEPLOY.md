# 🚀 クイックデプロイガイド

## Streamlit Community Cloudで5分でデプロイ

### ステップ1: GitHubにプッシュ（まだの場合）

```bash
git add .
git commit -m "デプロイ用の設定ファイルを追加"
git push origin main
```

### ステップ2: Streamlit Community Cloudにアクセス

1. [https://share.streamlit.io/](https://share.streamlit.io/) を開く
2. GitHubアカウントでログイン

### ステップ3: アプリを作成

1. 「New app」をクリック
2. 以下を入力：
   - **Repository**: `konnojp1995-hub/minpaku-project2`
   - **Branch**: `main`
   - **Main file path**: `src/main.py`
   - **App URL**: `minpaku-chatbot`（お好みで）
3. 「Deploy!」をクリック

### ステップ4: 環境変数を設定

デプロイ後（1-3分待つ）：

1. アプリの「⋮」メニュー → 「Settings」 → 「Secrets」
2. 以下を貼り付け：

```toml
GOOGLE_MAPS_API_KEY = "your_key_here"
GEMINI_API_KEY = "your_key_here"
GEOCODING_API_KEY = "your_key_here"
MAX_FILE_SIZE_MB = 10
```

3. 「Save」をクリック

### 完了！

数秒後、アプリが以下のURLで利用可能になります：
```
https://minpaku-chatbot.streamlit.app
```

---

## その他のデプロイ方法

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

