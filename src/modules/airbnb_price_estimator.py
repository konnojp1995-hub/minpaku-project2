"""
Airbnb価格推定モジュール
Geminiを使用してAirbnbの1泊あたりの平均単価を推定する機能を提供
"""
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
import pandas as pd
from .utils import log_error, log_info, log_warning

# Google Geminiのインポート
try:
    import google.generativeai as genai
    try:
        from google.generativeai.types import Tool
    except ImportError:
        # Toolクラスが利用できない場合は、辞書形式を使用
        Tool = None
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    Tool = None


class AirbnbPriceEstimator:
    """Airbnbの1泊あたりの平均単価を推定するクラス"""
    
    def __init__(self, gemini_api_key: str = ""):
        """
        初期化
        
        Args:
            gemini_api_key: Gemini APIキー
        """
        self.gemini_api_key = gemini_api_key
        self.gemini_available = GEMINI_AVAILABLE
        
        if not self.gemini_available:
            self.gemini_init_error = "google-generativeaiライブラリがインストールされていません"
        elif not self.gemini_api_key:
            self.gemini_init_error = "Gemini APIキーが未設定です"
            self.gemini_available = False
        else:
            # genai.configure()とモデルの初期化は完全に遅延させる（実際にAPIを使用する時まで待つ）
            # 起動時の不要なAPIコールを完全に避けるため、すべての初期化を遅延
            self.gemini_model = None
            self.gemini_model_name = None  # 使用するモデル名（遅延初期化時に決定）
            self.gemini_init_error = ""
            self._gemini_configured = False  # configure()が呼ばれたかどうか
    
    def _call_gemini(self, prompt: str, use_google_search: bool = False) -> Tuple[str, Optional[object]]:
        """
        Gemini APIを呼び出す（Google Search grounding対応）
        
        Args:
            prompt: プロンプト
            use_google_search: Google Search groundingを使用するか
            
        Returns:
            (レスポンステキスト, レスポンスオブジェクト)のタプル
        """
        if not self.gemini_available:
            return ("Gemini APIが利用できません", None)
        
        # genai.configure()とモデルの初期化を遅延させる（初回API呼び出し時まで待つ）
        if not self._gemini_configured:
            try:
                # ロギングを抑制してモデル検索のログを非表示にする
                import logging
                logging.getLogger('google.generativeai').setLevel(logging.WARNING)
                logging.getLogger('google.ai.generativelanguage').setLevel(logging.WARNING)
                genai.configure(api_key=self.gemini_api_key)
                self._gemini_configured = True
            except Exception as e:
                self.gemini_available = False
                self.gemini_init_error = str(e)
                log_error(f"Gemini初期化エラー: {str(e)}")
                return (f"エラー: {self.gemini_init_error}", None)
        
        if self.gemini_model is None:
            # gemini-2.0-flashを固定値として使用（モデル検索を避けるため、直接モデル名を指定）
            try:
                # モデル名を明示的に指定（models/プレフィックス付き、位置引数で指定）
                self.gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
                self.gemini_model_name = 'gemini-2.0-flash'
                log_info("Geminiモデルを初期化しました: gemini-2.0-flash")
            except Exception as e:
                error_str = str(e)
                # 429エラー（クォータ超過）の場合は即座に停止
                if "429" in error_str or "quota" in error_str.lower():
                    self.gemini_available = False
                    self.gemini_init_error = "Gemini APIのクォータ制限に達しています。しばらく待ってから再試行してください。"
                    log_error(self.gemini_init_error)
                    return (f"エラー: {self.gemini_init_error}", None)
                self.gemini_available = False
                self.gemini_init_error = f"Geminiモデル（gemini-2.0-flash）の初期化に失敗: {error_str}"
                log_error(self.gemini_init_error)
                return (f"エラー: {self.gemini_init_error}", None)
        
        try:
            tools_config = None
            if use_google_search:
                log_info("Google検索によるグラウンディング機能を使用して、Airbnb公式サイトの公開情報を検索します")
                
                # Google Search groundingを有効化（1回のみ試行してAPIコールを削減）
                try:
                    log_info("Google検索ツールを有効化します...")
                    response_obj = None
                    
                    # クォータ制限エラーをチェックするためのフラグ
                    quota_error_detected = False
                    
                    # 方法1: 辞書形式を最初に試行（最も一般的な方法）
                    try:
                        tools_config = [
                            {
                                "google_search": {}
                            }
                        ]
                        response_obj = self.gemini_model.generate_content(
                            prompt,
                            tools=tools_config
                        )
                        log_info("✅ Google検索によるグラウンディング機能を使用しました（辞書形式）")
                    except Exception as e1:
                        error_str = str(e1)
                        # クォータ制限エラーの場合は再試行しない
                        if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                            quota_error_detected = True
                            log_warning(f"⚠️ Gemini APIのクォータ制限に達しました: {error_str}")
                            raise  # エラーを再発生させて、呼び出し元で処理
                        log_warning(f"辞書形式が失敗しました: {error_str}")
                        # 通常モードで実行（1回のみ）
                        log_info("通常モードで実行します")
                        response_obj = self.gemini_model.generate_content(prompt)
                    
                    if response_obj is None and not quota_error_detected:
                        response_obj = self.gemini_model.generate_content(prompt)
                        
                except Exception as e:
                    error_str = str(e)
                    # クォータ制限エラー（429）の場合は即座に停止し、後続の呼び出しを防ぐ
                    if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                        self.gemini_available = False
                        self.gemini_init_error = "Gemini APIのクォータ制限に達しています。しばらく待ってから再試行してください。"
                        log_error(self.gemini_init_error)
                        return (f"エラー: {self.gemini_init_error}", None)
                    log_warning(f"Google検索ツールの設定に失敗しました。通常モードで実行します: {error_str}")
                    response_obj = self.gemini_model.generate_content(prompt)
            else:
                response_obj = self.gemini_model.generate_content(prompt)
            
            # レスポンステキストを取得
            if response_obj and response_obj.text:
                response_text = response_obj.text.strip()
                
                # Google検索の使用状況を確認
                if use_google_search:
                    log_info("Google検索の使用状況を確認")
                    grounding_metadata = None
                    
                    # grounding_metadataはcandidates内のCandidateオブジェクトに含まれる
                    if hasattr(response_obj, 'candidates') and response_obj.candidates:
                        candidate = response_obj.candidates[0]
                        if hasattr(candidate, 'grounding_metadata'):
                            grounding_metadata = candidate.grounding_metadata
                    
                    if grounding_metadata:
                        # grounding_metadataはprotobufオブジェクトなので、属性としてアクセス
                        chunks = []
                        if hasattr(grounding_metadata, 'grounding_chunks'):
                            chunks = list(grounding_metadata.grounding_chunks)
                        elif hasattr(grounding_metadata, 'get') and callable(grounding_metadata.get):
                            chunks = grounding_metadata.get('grounding_chunks', [])
                        
                        log_info(f"grounding_metadata取得: {len(chunks)}件のチャンク")
                        
                        # grounding_metadataからURLを抽出してログに表示
                        urls_found = []
                        for chunk in chunks:
                            try:
                                # chunkはprotobufオブジェクトの可能性がある
                                web = None
                                if hasattr(chunk, 'web'):
                                    web = chunk.web
                                elif isinstance(chunk, dict) and 'web' in chunk:
                                    web = chunk['web']
                                
                                if web:
                                    uri = None
                                    if hasattr(web, 'uri'):
                                        uri = web.uri
                                    elif isinstance(web, dict) and 'uri' in web:
                                        uri = web['uri']
                                    
                                    if uri:
                                        urls_found.append(uri)
                            except Exception as e:
                                # チャンクの処理でエラーが発生しても続行
                                continue
                        
                        if urls_found:
                            log_info(f"grounding_metadataから抽出したURL数: {len(urls_found)}件（最初の3件を表示）")
                            for i, url in enumerate(urls_found[:3]):
                                log_info(f"  [{i+1}] {url}")
                        else:
                            log_info("ℹ️ grounding_metadataからURLが見つかりませんでした（Google検索結果から情報を取得している可能性があります）")
                    else:
                        log_info("ℹ️ grounding_metadataがありません（Google検索は使用されていますが、メタデータは利用できない可能性があります）")
                
                return (response_text, response_obj)
            else:
                return ("応答を取得できませんでした", response_obj)
        except Exception as e:
            error_str = str(e)
            # 429エラー（クォータ超過）の場合は即座に停止し、後続の呼び出しを防ぐ
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                self.gemini_available = False
                self.gemini_init_error = "Gemini APIのクォータ制限に達しています。しばらく待ってから再試行してください。"
                error_msg = f"Gemini APIのクォータ制限に達しました。無料プランでは1日50リクエストまでです。しばらく待ってから再度お試しください。"
                log_error(error_msg)
                return (error_msg, None)
            error_msg = f"Gemini API呼び出しエラー: {error_str}"
            log_error(error_msg)
            return (error_msg, None)
            return (f"エラー: {error_msg}", None)
    
    def extract_address_to_cho(self, address: str) -> str:
        """
        住所から町名レベル（丁目を含まない）を抽出
        
        Args:
            address: 住所文字列
            
        Returns:
            町名レベルの住所
        """
        if not address:
            return address
        
        # 都道府県部分を抽出
        prefecture_match = re.search(r'^([^都道府県]+[都道府県])', address)
        if not prefecture_match:
            return address
        
        prefecture = prefecture_match.group(1)
        remaining = address[len(prefecture):]
        
        # 市町村区を探す（最初に見つかったものを使用）
        city_match = re.search(r'([^市区]+[市区])', remaining)
        if city_match:
            city = city_match.group(1)
            city_end_pos = city_match.end()
            after_city = remaining[city_end_pos:]
            
            # 町名を探す（丁目を含まない）
            town_match = re.search(r'([^0-9０-９一-九十丁目]+[町])', after_city)
            if town_match:
                town = town_match.group(1)
                # 丁目や数字を除去
                town = re.sub(r'[0-9０-９一-九十]+[丁目].*$', '', town)
                town = re.sub(r'[0-9０-９]+$', '', town)
                return prefecture + city + town.strip()
            else:
                # 町名が見つからない場合は市まで
                return prefecture + city
        
        return address
    
    def extract_address_to_city_or_ward(self, address: str) -> str:
        """
        住所から市または区レベル（都道府県を含む）を抽出
        
        Args:
            address: 住所文字列
            
        Returns:
            市または区レベルの住所
        """
        # 都道府県部分を抽出
        prefecture_match = re.search(r'^([^都道府県]+[都道府県])', address)
        if not prefecture_match:
            return address
        
        prefecture = prefecture_match.group(1)
        remaining = address[len(prefecture):]
        
        # 市または区を探す
        city_match = re.search(r'([^市区]+[市区])', remaining)
        if city_match:
            city_or_ward = city_match.group(1)
            return prefecture + city_or_ward
        
        return address
    
    def calculate_occupancy_from_area(self, area: Optional[float]) -> int:
        """
        面積から宿泊人数を計算
        
        Args:
            area: 延べ床面積（m²）
            
        Returns:
            推定宿泊人数（1〜10の範囲）
        """
        if area is None or area <= 0:
            return 1
        
        occupancy = round(area / 12)
        return max(1, min(10, occupancy))
    
    def get_next_next_month_week(self) -> Dict[str, str]:
        """
        翌々月の月曜〜日曜の1週間の日付範囲を取得
        
        Returns:
            {'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}の辞書
        """
        today = datetime.now()
        # 翌々月を計算
        if today.month >= 11:
            next_next_month = today.replace(year=today.year + 1, month=today.month - 10, day=1)
        else:
            next_next_month = today.replace(month=today.month + 2, day=1)
        
        # 月曜日を探す（翌々月の最初の月曜日）
        first_monday = next_next_month
        while first_monday.weekday() != 0:  # 0 = Monday
            first_monday += timedelta(days=1)
        
        # 日曜日を計算（月曜日の6日後）
        sunday = first_monday + timedelta(days=6)
        
        return {
            'start_date': first_monday.strftime('%Y-%m-%d'),
            'end_date': sunday.strftime('%Y-%m-%d')
        }
    
    def _extract_price_number(self, price_str: str) -> float:
        """価格文字列から数値を抽出"""
        if not price_str:
            return 0.0
        price_str = str(price_str)
        # ¥、,、円などを除去
        price_str = price_str.replace('¥', '').replace(',', '').replace('円', '').strip()
        try:
            return float(price_str)
        except:
            return 0.0
    
    def _extract_price_range(self, range_str: str) -> Tuple[float, float]:
        """価格範囲文字列から最小値と最大値を抽出"""
        if not range_str:
            return (0.0, 0.0)
        range_str = str(range_str)
        # ¥◯◯◯〜¥◯◯◯の形式から抽出
        match = re.search(r'¥?([0-9,]+).*?¥?([0-9,]+)', range_str)
        if match:
            min_price = self._extract_price_number(match.group(1))
            max_price = self._extract_price_number(match.group(2))
            return (min_price, max_price)
        return (0.0, 0.0)
    
    def _extract_number(self, num_str: str) -> int:
        """数値文字列から整数を抽出"""
        if not num_str:
            return 0
        num_str = str(num_str)
        # 数字以外を除去
        num_str = re.sub(r'[^0-9]', '', num_str)
        try:
            return int(num_str)
        except:
            return 0
    
    def estimate_price(self, address: str, area: Optional[float] = None) -> Dict:
        """
        Airbnbの1泊あたりの平均単価を推定
        
        Args:
            address: 物件の住所
            area: 延べ床面積（m²）
            
        Returns:
            推定結果の辞書
        """
        if not self.gemini_available:
            return {
                'success': False,
                'error': 'Gemini APIが利用できません',
                'average_price_median': None,
                'price_range': None,
                'property_count': None,
                'popularity_memo': None
            }
        
        # 住所から各レベルを抽出（丁目レベルは使用しない）
        address_to_cho = self.extract_address_to_cho(address)
        address_to_city_or_ward = self.extract_address_to_city_or_ward(address)
        
        # 宿泊人数を計算
        occupancy = self.calculate_occupancy_from_area(area)
        
        # プロンプトを作成する関数
        def create_search_prompt(search_addr: str, level: str) -> str:
            return f"""# 【指示】Airbnb検索 → 上位物件URL抽出＋中央値算出

以下の条件に沿って、Google検索機能を使用してAirbnb公式サイト（https://www.airbnb.jp）を検索し、
検索結果やリスティングページから確認できる**正確な物件URL**を最大20件まで抽出し、
そのURLを用いて「1泊あたりの平均単価（中央値）」を算出してください。

**重要：Google検索機能を使用して、実際にAirbnb公式サイトの検索結果やリスティングページをブラウズし、そこで見つかった実在のURLと情報を抽出してください。**

## 検索条件

1. 場所：{search_addr}（マイソクOCRで抽出した住所の「{level}」レベルを使用）

2. 宿泊日：実行時の現在日付から数えて3か月以内の間で1週間宿泊可能なリスティングを抽出対象とすること（例：現在が9月10日なら対象は11月末までの間で1週間、すなわち2025-9-10〜2025-11-30の範囲内で7日間連続で宿泊可能なリスティングを探す）

**重要：検索範囲が広い（市レベル）場合は、検索条件を緩和してください。**
- 市レベルや区レベルでの検索時は、特定の1週間ではなく、3か月以内で宿泊可能な期間があれば、その期間の1泊あたりの価格を参考にしてください
- 完全に1週間連続宿泊可能な物件が見つからない場合は、1泊〜数泊の宿泊可能な物件の価格情報も参考にしてください
- 地域の価格相場を把握するため、利用可能期間の価格情報を広く収集してください

3. 宿泊人数：{occupancy}人（物件面積から自動推定：面積(m²) ÷ 12、1人未満は1人、上限10人）

    4. 物件タイプ：すべての物件タイプを対象とします（まるまり貸切、プライベートルーム、シェアルームなど、すべてのタイプを含む）

5. 除外：宿泊人数が物件規模に対して過剰または過少な物件

## 宿泊人数の推定式（自動）

- 面積(m²)が物件に記載されている場合は次で算出：
    推定宿泊人数 = round( 面積(m²) ÷ 12 )
- 補正：1人未満は1人に繰り上げ、上限は10人
- 取得できない場合は「表示されているホストの定員（listed capacity）」を利用する
- 対象フィルタ：調査条件（{occupancy}名）に近い物件のみ採用（listed capacity または推定宿泊人数が ±2 内を優先）

## 抽出ルール（必須・厳格に遵守）

### 【最重要】URL生成の完全禁止

**⚠️ 絶対に守るべきルール：URLは生成ではなく、必ずAirbnb公式の検索結果／リスティングページから取得した実在のURLを貼ること。**

**🚫 禁止事項（絶対に守ること）：**
- ❌ **AIがURLを作成・生成することは絶対に禁止**
- ❌ **部屋IDを推測・創作することは禁止**
- ❌ **連番や規則的な数字でURLを構成することは禁止**
- ❌ **仮想的なURLや推測したURLを出力することは禁止**
- ❌ **例示されたURLをそのままコピーすることは禁止（例示は形式を示すため）**

**✅ 許可事項（必ず従うこと）：**
- ✅ **grounding_metadataから取得したURLのみを使用（最優先）**
- ✅ **Google検索結果で実際に見つかったAirbnbのURLのみを使用**
- ✅ **検索スニペットに表示されている実在のURLのみを使用**
- ✅ **検索結果やリスティングページで実際に表示されているURLのみを使用**

**重要：このAI応答内でURLを「作成」する行為は一切禁止です。grounding_metadataまたはGoogle検索結果から実際に見つかったURLをそのまま使用してください。**

2. **URL取得の優先順位（必ずこの順序で、この順序のみ使用すること）**：
  1. **grounding_metadataから取得したURI（`chunk.web.uri`）を最優先で使用**
  2. Google検索結果ページに表示されているAirbnbのリンクURL
  3. 検索スニペットに表示されているURL
  4. `link rel="canonical"` または `og:url` メタタグ（存在する場合）

**重要：grounding_metadataから取得したURLを最優先で使用してください。grounding_metadataにURLがない場合は、Google検索結果や検索スニペットから取得したAirbnbの実在URLを使用してください。**

3. **リダイレクト処理**：
  - grounding_metadataや検索スニペットに中間リダイレクト（`google.com/url?q=...`等）がある場合
  - **必ず最終到達先（最終URL）を取得すること**
  - 中間URLではなく、Airbnbの実際のページURL（`www.airbnb.jp/rooms/...`）を返すこと

4. **URL補完のルール（注意）**：
  - 補完は**既に取得した実在URLに対してのみ**行うこと
  - `/rooms/12345` → `https://www.airbnb.jp/rooms/12345`（実URLから取得した場合のみ）
  - `www.airbnb.jp/...` → `https://www.airbnb.jp/...`（実URLから取得した場合のみ）
  - **部屋ID（例：12345）は絶対に創作しないこと**

**疑わしいURLは `validated: false` として返すか、出力しないこと。**

## 検証ルール（各URLごとに）

**重要：検索結果やリスティングページから以下の情報を必ず取得すること：**
- **タイトル（Listing title）**：物件名。検索結果でゲストに表示される名前。
- **概要説明（Summary / Short description）**：タイトル下などに表示される短いキャッチ文。
- **価格（price_per_night）**：1泊あたりの料金（税・手数料除く）

出力するURLは各々について次のメタ情報を付与する（JSONオブジェクトの形）：
- url (文字列、クリーンアップ済み)
- title (タイトル / Listing title：物件名。検索結果でゲストに表示される名前)
- summary (概要説明 / Summary / Short description：タイトル下などに表示される短いキャッチ文)
- room_id (数値ID が取れれば)
- area_m2 (取得できれば数値)
- listed_capacity (ホストが表示する定員)
- estimated_guests (area ÷ 12 の結果 or listed_capacity)
- price_per_night (該当週の1泊あたり料金、税・手数料除く。価格は検索結果で明示されている値を優先)
- reviews_count (取得できれば)
- source (e.g. google_search / airbnb_search_snippet / grounding_metadata)
- validated (boolean; 実URLかつアクセス確認済みなら true、確認できなければ false)
- notes (短い補足、例：「面積記載なしでlisted_capacity使用」など)

## 集計ルール（中央値算出）

- 対象は上記フィルタを通過し `validated==true` のもの優先で最大20件（20件に満たない場合は入手可能件数で算出）。
- 価格は各物件の「1泊あたり料金（税・手数料除く）」を使用。
- 統計指標は**中央値（Median）**を採用。あわせて最小値・最大値（価格範囲）を出す。
- 出力に「推定根拠」（どの検索結果／スニペット／地域統計を使ったか）を簡潔に添える。

## 出力形式（厳密）

**1) 最初に抽出した物件リスト（最大20件）を JSON 配列で出力**（上記のメタ情報を各オブジェクトに含める）：

```json
[
  {{
    "url": "grounding_metadataから取得した実際のURLをここに貼り付けてください",
    "title": "物件タイトル（検索結果から取得、Listing title）",
    "summary": "タイトル下などに表示される短いキャッチ文（Summary / Short description）",
    "room_id": "検索結果から取得した実在の部屋ID",
    "area_m2": 25,
    "listed_capacity": {occupancy},
    "estimated_guests": {occupancy},
    "price_per_night": 15000,
    "reviews_count": 24,
    "source": "grounding_metadata",
    "validated": true,
    "notes": "grounding_metadataから取得した実在URL"
  }},
  ...
]
```

**⚠️ 重要：上記の例示URLは使用禁止です。必ずgrounding_metadata、Google検索結果、検索スニペットから実際に見つかった実在のURLのみを使用してください。例示URLをコピーして使用することは絶対に禁止です。**

**2) 次に、最終集計結果を以下の指定JSONで出力：**

```json
{{
  "平均単価_中央値": "¥◯◯◯◯",
  "価格範囲": "¥◯◯◯〜¥◯◯◯",
  "宿泊件数": "◯件",
  "人気度メモ": "レビュー傾向や地域特性を簡潔に記述",
  "推定根拠": "Google検索によりAirbnb公式サイトの公開情報を検索し、grounding_metadataから取得した実在のリスティング情報に基づいて推定しました。"
}}
```

## 備考（重要・必読）

- **⚠️ 絶対禁止事項：「AIがURLを作る」ことは禁止。URLは必ず検索結果やリスティングページから取得した実在のURLを貼ること。**
- **重要：URLは必ずgrounding_metadata、Google検索結果、検索スニペットから実際に見つかったURLのみを使用してください。**
- **grounding_metadataからURLが見つからない場合は、Google検索結果や検索スニペットから取得した実在URLを使用してください。**
- **すべてのソースからURLが見つからない場合のみ、物件数を0件として返してください。**
- **⚠️ 注意：例示されたURL（例：`https://www.airbnb.jp/rooms/1088306445534102381`）は形式を示すためのものであり、実際に使用してはいけません。**
- 疑わしいURLや生成された可能性があるURLは `validated:false` として返すか、出力しないこと。
- grounding_metadataから取得したURLを最優先で使用し、見つからない場合はGoogle検索結果や検索スニペットから取得した実在URLを使用してください。
- 必要なら「不足件数（例：取得件数が10件に満たない）」を明示して、その理由を `notes` に記載すること（例：「該当条件の物件が少ない」「面積情報が多く欠如」等）。
- 出力は **最初に物件リストJSON、続けて集計JSON** の順で（両方とも機械可読なJSON形式で）返してください。

**重要：JSONのみを返してください。説明文や補足は不要です。2つのJSON配列/オブジェクトを順番に返してください。**"""
        
        # 再検索ロジック: 町名レベル → 市または区レベル → 広域(都道府県/全国) の最大3段階で検索
        max_retries = 3
        retry_count = 0
        result = None
        property_list = None
        response_text = None
        response_obj = None
        response = None
        final_search_level = None  # 最終的に使用した検索レベルを記録
        final_search_address = None  # 最終的に使用した検索住所を記録
        
        try:
            while retry_count < max_retries:
                try:
                    if retry_count == 0:
                        # 1回目: 町名レベル（なければ市区町村、さらに全住所）
                        search_address = address_to_cho or address_to_city_or_ward or address or "日本"
                        search_level = "町名"
                        log_info(f"Airbnb価格推定を開始（{search_level}レベル）: 住所={search_address}, 宿泊人数={occupancy}人")
                    elif retry_count == 1:
                        # 2回目: 市または区レベル（なければ全住所）
                        search_address = address_to_city_or_ward or address or "日本"
                        search_level = "市または区"
                        log_info(f"リスティングが見つかりませんでした。検索範囲を拡大します（{search_level}レベル）: 住所={search_address}")
                    else:
                        # 3回目: 広域（都道府県または全国）
                        # addressから都道府県を推定（単純に先頭の県/都/府/道を抽出）
                        prefecture_match = re.search(r'(北海道|.+?[都道府県])', address or '')
                        search_address = prefecture_match.group(1) if prefecture_match else "日本"
                        search_level = "広域"
                        log_info(f"さらに検索範囲を拡大します（{search_level}レベル）: 住所={search_address}")
                    
                    prompt = create_search_prompt(search_address, search_level)
                    
                    # Gemini APIを呼び出し、レスポンステキストとレスポンスオブジェクトを取得
                    response_text, response_obj = self._call_gemini(prompt, use_google_search=True)
                    response = response_text
                    
                    # デバッグ用：レスポンスの最初の500文字をログに出力（検索結果確認用）
                    if response:
                        response_preview = response[:500] if len(response) > 500 else response
                        log_info(f"🔍 Geminiレスポンス（{search_level}レベル）プレビュー: {response_preview}...")
                    
                    # クォータ制限エラー（429）の場合は再試行しない
                    is_quota_error = "429" in str(response) or "quota" in str(response).lower() or "rate" in str(response).lower() or "クォータ" in str(response)
                    
                    if not response or response.startswith("エラー") or response == "Gemini APIが利用できません":
                        # クォータ制限エラーの場合は即座に終了
                        if is_quota_error:
                            return {
                                'success': False,
                                'error': response,
                                'average_price_median': None,
                                'price_range': None,
                                'property_count': None,
                                'popularity_memo': None
                            }
                        # その他のエラーの場合のみ再試行
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            continue
                        else:
                            return {
                                'success': False,
                                'error': response,
                                'average_price_median': None,
                                'price_range': None,
                                'property_count': None,
                                'popularity_memo': None
                            }
                    
                    # JSONを抽出（新形式：物件リストJSON配列 → 集計JSON）
                    # 1. 最初に物件リストのJSON配列を探す
                    property_list_patterns = [
                        (r'```json\s*(\[.*?\])\s*```', 1, re.DOTALL),
                        (r'(\[[\s\S]*?"url"[\s\S]*?"validated"[\s\S]*?\])', 1, re.DOTALL),
                        (r'(\[[\s\S]*?\])\s*\{', 1, re.DOTALL),
                    ]
                    
                    property_list = None
                    property_list_str = None
                    
                    for pattern, group_idx, flags in property_list_patterns:
                        match = re.search(pattern, response, flags)
                        if match:
                            try:
                                property_list_str = match.group(group_idx)
                                property_list = json.loads(property_list_str)
                                if isinstance(property_list, list) and len(property_list) > 0:
                                    log_info(f"物件リストJSONを抽出: {len(property_list)}件")
                                    break
                            except:
                                property_list = None
                                property_list_str = None
                                continue
                    
                    # 2. 集計結果のJSONを探す（平均単価_中央値を含む）
                    summary_patterns = [
                        (r'```json\s*(\{.*?"平均単価_中央値".*?\})\s*```', 1, re.DOTALL),
                        (r'(\{[^{}]*"平均単価_中央値"[^{}]*\})', 1, re.DOTALL),
                        (r'\{[\s\S]*?"平均単価_中央値"[\s\S]*?\}', 0, re.DOTALL),
                    ]
                    
                    result = None
                    json_str = None
                    
                    for pattern, group_idx, flags in summary_patterns:
                        match = re.search(pattern, response, flags)
                        if match:
                            try:
                                if group_idx > 0:
                                    json_str = match.group(group_idx)
                                else:
                                    json_str = match.group(0)
                                result = json.loads(json_str)
                                if '平均単価_中央値' in result:
                                    log_info("集計結果JSONを抽出")
                                    break
                            except:
                                result = None
                                json_str = None
                                continue
                    
                    # リスティングが見つかったかチェック（有効な物件があるかどうか）
                    found_listings = False
                    has_valid_listings = False
                    
                    # 物件リストをチェックして、有効な物件があるか確認
                    if property_list and isinstance(property_list, list) and len(property_list) > 0:
                        log_info(f"📋 物件リストを確認: {len(property_list)}件のエントリが見つかりました")
                        for idx, prop in enumerate(property_list):
                            if isinstance(prop, dict):
                                title = prop.get('title', '')
                                validated = prop.get('validated', False)
                                price_per_night = prop.get('price_per_night', None)
                                
                                # デバッグ用：最初の3件の詳細をログに出力
                                if idx < 3:
                                    log_info(f"  [{idx+1}] title={title}, validated={validated}, price={price_per_night}")
                                
                                if title and title not in ['該当物件なし', 'N/A', '', '物件が見つかりませんでした']:
                                    if validated or (price_per_night is not None and price_per_night > 0):
                                        has_valid_listings = True
                                        log_info(f"✅ 有効な物件を発見: {title}")
                                        break
                        
                        if not has_valid_listings:
                            log_warning(f"⚠️ {search_level}レベルで物件リストは見つかりましたが、有効な物件がありませんでした。検索範囲を拡大します。")
                            # デバッグ用：物件リストの内容をログに出力
                            if property_list:
                                log_info(f"📋 物件リストのサンプル（最初の3件）: {json.dumps(property_list[:3], ensure_ascii=False, indent=2)}")
                    else:
                        log_warning(f"⚠️ {search_level}レベルで物件リストが見つかりませんでした。レスポンスにJSON配列が含まれていない可能性があります。")
                    
                    # 集計結果から物件数を確認
                    if not has_valid_listings and result and result.get('宿泊件数'):
                        property_count_str = result.get('宿泊件数', '0件')
                        property_count_num = self._extract_number(property_count_str)
                        if property_count_num > 0:
                            has_valid_listings = True
                    
                    # 価格が有効かどうかも確認
                    if not has_valid_listings and result:
                        median_price_str = result.get('平均単価_中央値', '¥0')
                        if median_price_str and median_price_str.upper() not in ['¥0', '0', 'N/A', '']:
                            median_price_val = self._extract_price_number(median_price_str)
                            if median_price_val > 0:
                                has_valid_listings = True
                    
                    found_listings = has_valid_listings
                    
                    # 有効なリスティングが見つかった場合はループを抜ける
                    if found_listings:
                        log_info(f"✅ {search_level}レベルで有効なリスティングが見つかりました")
                        final_search_level = search_level
                        final_search_address = search_address
                        break
                    else:
                        # リスティングが見つからなかった場合、次のレベルで再検索
                        if retry_count < max_retries - 1:
                            log_warning(f"⚠️ {search_level}レベルで有効なリスティングが見つかりませんでした。検索範囲を拡大します。")
                            retry_count += 1
                        else:
                            log_warning(f"⚠️ {search_level}レベルでも有効なリスティングが見つかりませんでした。")
                            break
                except Exception as e:
                    log_error(f"検索エラー ({search_level}レベル): {str(e)}")
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        continue
                    else:
                        raise
            
            # ループを抜けた後の処理
            if result:
                try:
                    # 平均単価_中央値から数値を抽出
                    median_price_str = result.get('平均単価_中央値') or '¥0'
                    if median_price_str is None:
                        median_price_str = '¥0'
                    
                    # "N/A"の場合は物件が見つからなかったことを意味する（正常な状態）
                    if median_price_str.upper() == 'N/A':
                        log_warning("物件が見つかりませんでした（median_price_str: N/A）。デフォルト価格を使用します。")
                        median_price = 0
                    else:
                        median_price = self._extract_price_number(median_price_str)
                    
                    # 物件数が0件で価格が抽出できない場合は、正常な状態として扱う（エラーではない）
                    property_count_str = result.get('宿泊件数') or '0件'
                    if property_count_str is None:
                        property_count_str = '0件'
                    property_count = self._extract_number(property_count_str)
                    
                    # 物件が見つからなかった場合（property_count == 0 または median_price == 0）
                    if property_count == 0 or median_price == 0:
                        log_warning(f"物件が見つかりませんでした（物件数: {property_count}件, 中央値: {median_price_str}）。デフォルト価格を使用します。")
                        median_price = 0
                    
                    # 価格範囲から最小値と最大値を抽出
                    price_range_str = result.get('価格範囲') or '¥0〜¥0'
                    if price_range_str is None:
                        price_range_str = '¥0〜¥0'
                    
                    if price_range_str.upper() == 'N/A':
                        price_range_str = '¥0〜¥0'
                    
                    min_price, max_price = self._extract_price_range(price_range_str)
                    
                    # 物件リストからタイトル、概要説明、価格を抽出してログに表示
                    listing_info_list = []
                    if property_list and isinstance(property_list, list):
                        for prop in property_list:
                            if isinstance(prop, dict):
                                title = prop.get('title', 'タイトル不明')
                                summary = prop.get('summary', None)
                                price_per_night = prop.get('price_per_night', None)
                                source = prop.get('source', 'unknown')
                                validated = prop.get('validated', False)
                                
                                # 価格をフォーマット
                                price_str = '価格不明'
                                if price_per_night is not None:
                                    try:
                                        if isinstance(price_per_night, (int, float)):
                                            price_str = f"¥{int(price_per_night):,}"
                                        elif isinstance(price_per_night, str):
                                            price_num = self._extract_price_number(price_per_night)
                                            if price_num > 0:
                                                price_str = f"¥{price_num:,}"
                                    except:
                                        price_str = str(price_per_night)
                                
                                summary_str = summary if summary else ''
                                
                                listing_info_list.append({
                                    'title': title,
                                    'summary': summary_str,
                                    'price': price_str,
                                    'source': source,
                                    'validated': validated
                                })
                    
                    # 表示用の物件リストを準備（タイトル、概要、価格）
                    listing_display_data = []
                    if listing_info_list:
                        for info in listing_info_list:
                            listing_display_data.append({
                                'タイトル': info['title'],
                                '概要': info['summary'] if info['summary'] else '',
                                '価格': info['price']
                            })
                    
                    # 推定根拠を取得
                    estimation_basis = result.get('推定根拠', '')
                    
                    # リスティング情報の表を表示（推定根拠の前に表示）
                    if listing_display_data and len(listing_display_data) > 0:
                        df_listings = pd.DataFrame(listing_display_data)
                        st.dataframe(df_listings, use_container_width=True)
                    
                    # 推定根拠をログに表示
                    if estimation_basis:
                        log_info(f"📊 推定根拠: {estimation_basis}")
                    
                    log_info(f"Airbnb価格推定成功: {int(median_price)}円")
                    
                    return {
                        'success': True,
                        'average_price_median': median_price,
                        'average_price_median_str': median_price_str,
                        'price_range': price_range_str,
                        'min_price': min_price,
                        'max_price': max_price,
                        'property_count': property_count,
                        'property_count_str': property_count_str,
                        'popularity_memo': result.get('人気度メモ', ''),
                        'estimation_basis': estimation_basis,
                        'search_level': final_search_level,
                        'search_address': final_search_address,
                        'listing_data': listing_display_data,
                        'raw_response': response
                    }
                except json.JSONDecodeError as e:
                    log_error(f"JSON解析エラー: {str(e)}, レスポンス: {response}")
                    return {
                        'success': False,
                        'error': f'JSON解析エラー: {str(e)}',
                        'average_price_median': None,
                        'price_range': None,
                        'property_count': None,
                        'popularity_memo': None,
                        'raw_response': response
                    }
            else:
                # resultがNoneの場合（すべての検索レベルで有効な物件が見つからなかった場合）
                log_warning("すべての検索レベルで有効な物件が見つかりませんでした。デフォルト価格を使用します。")
                return {
                    'success': True,
                    'average_price_median': 0,
                    'average_price_median_str': '¥0',
                    'price_range': '¥0〜¥0',
                    'min_price': 0,
                    'max_price': 0,
                    'property_count': 0,
                    'property_count_str': '0件',
                    'popularity_memo': '物件が見つかりませんでした',
                    'estimation_basis': 'すべての検索レベル（町名、市または区）で物件が見つかりませんでした',
                    'search_level': None,
                    'search_address': None,
                    'listing_data': [],
                    'raw_response': response if 'response' in locals() else ''
                }
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = f"Airbnb価格推定エラー: {str(e)}"
            log_error(error_msg)
            
            print(f"\n{'='*80}", file=sys.stderr)
            print(f"[Airbnb価格推定エラー] スタックトレース:", file=sys.stderr)
            print(error_trace, file=sys.stderr)
            print(f"{'='*80}\n", file=sys.stderr)
            
            error_trace_preview = error_trace.split('\n')[:20]
            st.error(f"エラー詳細（スタックトレース）:\n```\n" + "\n".join(error_trace_preview) + "\n```")
            
            return {
                'success': False,
                'error': str(e),
                'average_price_median': None,
                'price_range': None,
                'property_count': None,
                'popularity_memo': None,
                'raw_response': response if 'response' in locals() else ''
            }


def create_airbnb_price_estimator(gemini_api_key: str = "") -> AirbnbPriceEstimator:
    """
    Airbnb価格推定器を作成するファクトリー関数
    
    Args:
        gemini_api_key: Gemini APIキー
        
    Returns:
        AirbnbPriceEstimatorインスタンス
    """
    return AirbnbPriceEstimator(gemini_api_key=gemini_api_key)

