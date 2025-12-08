# 民泊開業検討者向けチャットボットツール

物件の適法性・採算性をワンストップで確認できるチャットボットツールです。マイソク画像（不動産広告画像）をアップロードするだけで、住所抽出→法令判定→収支シミュレーションまで行えます。

## 機能概要

### 1. 画像解析機能
- マイソク画像（JPG/PNG/PDF）からOCRで住所を自動抽出
- Tesseract と EasyOCR の両方に対応
- 複数候補がある場合は信頼度の高いものを採用

### 2. 住所・用途地域判定
- 住所から緯度経度へのジオコーディング
- Google Maps API または Geocoding.jp API を使用
- 用途地域GeoJSONデータとの照合で用途地域を判定

### 3. 法令判定
- 旅館業法・民泊新法・特区民泊の適法性を判定
- 用途地域に基づく自動判定
- 結果を「可能／要確認／不可」で表示

### 4. チェックリスト機能
- 消防法・建築基準法・接道義務等の留意点をチェックリスト形式で管理
- 進捗状況の可視化
- 必須項目と推奨項目の区別

### 5. 投資回収シミュレーション
- 稼働率30〜90％を10％刻みで計算
- 投資回収年数・損益分岐点を表形式で出力
- グラフによる可視化
- パラメータの手動編集可能

## ディレクトリ構成

```
minpaku-chatbot/
├── src/                          # ソースコード
│   ├── main.py                   # Streamlit UI
│   └── modules/                  # モジュール群
│       ├── ocr_extractor.py      # OCR住所抽出
│       ├── geocoder.py           # ジオコーディング
│       ├── zoning_checker.py     # 用途地域判定
│       ├── law_checker.py        # 法令判定
│       ├── checklist.py          # チェックリスト管理
│       ├── simulation.py         # 投資シミュレーション
│       └── utils.py              # ユーティリティ
├── data/                         # GeoJSONデータ
│   ├── tokyo/                    # 東京の用途地域データ
│   └── niigata/                  # 新潟の用途地域データ
├── rules.json                    # 法令ルール定義
├── requirements.txt              # 依存関係
└── env_sample.txt               # 環境変数サンプル
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`env_sample.txt`を参考に`.env`ファイルを作成し、APIキーを設定してください。

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Google Maps API Key (optional)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Geocoding.jp API Key (optional)
GEOCODING_API_KEY=your_geocoding_api_key_here

# Tesseract executable path (Windows)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 3. Tesseractのインストール

#### Windows
1. [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)をダウンロード・インストール
2. `.env`ファイルで`TESSERACT_CMD`を設定

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
```

### 4. アプリケーションの起動

**重要**: 仮想環境を有効化してから起動してください。

#### 推奨：起動スクリプトを使用（最も簡単）

**Windows（PowerShell）**
```powershell
.\run.ps1
```

**Windows（コマンドプロンプト）**
```cmd
run.bat
```

このスクリプトが仮想環境を自動で有効化し、Streamlitアプリを起動します。

#### 手動で起動する場合

**Windows（PowerShell）**
1. プロジェクトフォルダでPowerShellを開く
2. 仮想環境を有効化：
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Streamlitアプリを起動：
   ```powershell
   streamlit run src/main.py
   ```

**Windows（コマンドプロンプト）**
1. プロジェクトフォルダでコマンドプロンプトを開く
2. 仮想環境を有効化：
   ```cmd
   venv\Scripts\activate.bat
   ```
3. Streamlitアプリを起動：
   ```cmd
   streamlit run src/main.py
   ```

**macOS/Linux**
```bash
source venv/bin/activate
streamlit run src/main.py
```

#### 起動確認

仮想環境が正しく有効化されている場合、コマンドプロンプトの前に `(venv)` が表示されます：
```
(venv) PS C:\Users\konno\Projects\minpaku-chatbot>
```

#### トラブルシューティング

**PowerShellスクリプトが実行できない場合**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
を実行してから、再度 `.\run.ps1` を実行してください。

## 使用方法

### 1. 画像解析
1. 「📷 画像解析」タブで不動産広告画像をアップロード
2. 「住所を抽出」ボタンをクリック
3. 抽出された住所候補から選択

### 2. 住所・用途地域判定
1. 「📍 住所・用途地域」タブで住所を確認
2. 「ジオコーディング実行」ボタンで座標を取得
3. 「用途地域判定実行」ボタンで用途地域を判定

### 3. 法令判定
1. 「⚖️ 法令判定」タブで各法令の適法性を確認
2. 旅館業法・民泊新法・特区民泊の判定結果を確認

### 4. チェックリスト
1. 「✅ チェックリスト」タブで必要な確認項目をチェック
2. 進捗状況を確認し、必須項目を優先的に完了

### 5. 投資シミュレーション
1. 「💰 投資シミュレーション」タブでパラメータを設定
2. 初期費用・運用費用・収益パラメータを入力
3. 「シミュレーション実行」ボタンで結果を確認

## 主要モジュール

### OCRAddressExtractor
- 画像から住所を抽出するクラス
- TesseractとEasyOCRの両方に対応
- 前処理による精度向上

### Geocoder
- 住所から緯度経度を取得するクラス
- Google Maps APIとGeocoding.jp APIに対応
- 複数APIの自動切り替え

### ZoningChecker
- 用途地域を判定するクラス
- GeoJSONデータとの空間照合
- 都道府県別のデータ管理

### LawChecker
- 法令の適法性を判定するクラス
- rules.jsonに基づく判定ロジック
- 旅館業法・民泊新法・特区民泊に対応

### ChecklistManager
- チェックリストを管理するクラス
- 進捗状況の追跡
- 必須項目と推奨項目の区別

### InvestmentSimulator
- 投資回収シミュレーションを行うクラス
- 稼働率別の収益計算
- 損益分岐点の算出

## 注意事項

- このツールは参考情報を提供するものです。実際の事業計画では専門家への相談を推奨します。
- 法令は変更される可能性があります。最新の情報を確認してください。
- APIキーは適切に管理し、公開しないでください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## キャッシュ削除と再実行

アプリケーションのキャッシュを削除して再実行する手順は、[CACHE_CLEAR_GUIDE.md](./CACHE_CLEAR_GUIDE.md) を参照してください。

**クイックリセット（推奨）:**

**Windows（PowerShell）**
```powershell
.\clear_cache.ps1
.\run.ps1
```

**Windows（コマンドプロンプト）**
```cmd
clear_cache.bat
run.bat
```

## インターネットからアクセスする方法

このアプリケーションをインターネットからアクセスできるようにする方法については、[PUBLIC_ACCESS_GUIDE.md](./PUBLIC_ACCESS_GUIDE.md) を参照してください。

### クイックスタート

**ngrokを使用（最も簡単）:**
1. [ngrok](https://ngrok.com/download)をインストール
2. ngrokアカウントを作成して認証: `ngrok config add-authtoken YOUR_TOKEN`
3. `.\run_public.ps1` (PowerShell) または `run_public.bat` (コマンドプロンプト) を実行

詳細は [PUBLIC_ACCESS_GUIDE.md](./PUBLIC_ACCESS_GUIDE.md) を参照してください。

## 更新履歴

- v1.0.0: 初回リリース
  - 基本的な機能を実装
  - OCR住所抽出
  - 用途地域判定
  - 法令判定
  - チェックリスト機能
  - 投資シミュレーション

