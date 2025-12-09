"""
OCR住所抽出モジュール
マイソク画像から住所を抽出する機能を提供
"""
import os
import re
import numpy as np
from PIL import Image
from typing import List, Dict, Optional
import streamlit as st
from .utils import validate_file_size, log_error, log_info, log_warning

# すべての画像処理はPIL/numpyで行う（OpenCVは使用しない）

# OpenAIは使用しない（Geminiのみ使用）

# Google Geminiのインポートを試行
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    # インポート時はログを出力しない（初期化時に適切なエラーメッセージを表示）

# TesseractとEasyOCRは使用しない（Geminiのみ使用）


class OCRAddressExtractor:
    """OCRを使用して画像から住所を抽出するクラス"""
    
    def __init__(self, tesseract_cmd: str = "", ocr_mode: str = "gemini", openai_api_key: str = "", gemini_api_key: str = ""):
        """
        初期化（Geminiのみ使用）
        
        Args:
            tesseract_cmd: （使用しない、互換性のため残す）
            ocr_mode: OCRエンジンモード（常に"gemini"）
            openai_api_key: （使用しない、互換性のため残す）
            gemini_api_key: Gemini APIキー
        """
        self.gemini_available = GEMINI_AVAILABLE
        self.ocr_mode = "gemini"  # Geminiのみ使用
        self.gemini_api_key = gemini_api_key
        # gemini-2.0-flashを固定値として使用
        self.gemini_model_name = 'gemini-2.0-flash'
        
        # Geminiクライアントを初期化
        self.gemini_init_error = ""
        if not self.gemini_available:
            self.gemini_init_error = "google-generativeaiライブラリがインストールされていません。'pip install google-generativeai' でインストールしてください。"
        elif not self.gemini_api_key:
            self.gemini_init_error = "Gemini APIキーが未設定です。サイドバーで設定してください。"
            log_error("Gemini APIキーが未設定です")
            self.gemini_available = False
        if self.gemini_available:
            try:
                # バージョン情報のログ（デバッグ用）
                try:
                    libver = getattr(genai, "__version__", "unknown")
                    log_info(f"google-generativeai バージョン: {libver}")
                except Exception:
                    pass
                # genai.configure()とモデルの初期化は完全に遅延させる（実際にAPIを使用する時まで待つ）
                # 起動時の不要なAPIコールを完全に避けるため、すべての初期化を遅延
                self.gemini_model = None
                self._gemini_configured = False  # configure()が呼ばれたかどうか
            except Exception as e:
                self.gemini_init_error = str(e)
                log_error(f"Geminiの初期化に失敗しました: {self.gemini_init_error}")
                self.gemini_available = False
        
        # 住所パターンの正規表現（大幅改善版）
        self.address_patterns = [
            # 物件所在地から抽出（最優先）
            r'物件所在地\s*([^交通\n]*?)(?=\s*交通|$)',
            # 完全な住所パターン（都道府県 + 市区町村 + 町名 + 番地）
            r'([都道府県][^都道府県]*?[市区町村][^市区町村]*?[町字][^町字]*?[0-9\-]+)',
            # 都道府県 + 市区町村 + 町名（番地なし）
            r'([都道府県][^都道府県]*?[市区町村][^市区町村]*?[町字][^町字]*?)',
            # 市区町村 + 町名 + 番地
            r'([市区町村][^市区町村]*?[町字][^町字]*?[0-9\-]+)',
            # 市区町村 + 町名
            r'([市区町村][^市区町村]*?[町字][^町字]*?)',
            # 住所らしき文字列（都道府県名を含む、より柔軟）
            r'([都道府県][^都道府県]*?[市区町村][^市区町村]*?[町字][^町字]*?[0-9\-]*?)',
            # 郵便番号付き住所
            r'〒[0-9\-]+\s*([^TEL\n]*?)(?=\s*TEL|$)',
        ]
    
    def extract_text_gemini(self, image: np.ndarray) -> List[Dict]:
        """
        Geminiを使用してテキストを抽出
        
        Args:
            image: 入力画像
            
        Returns:
            抽出されたテキストと信頼度のリスト
        """
        if not self.gemini_available or not self.gemini_api_key:
            return []
        
        # 画像は既にRGB形式であると仮定（PILで読み込んでいるため）
        
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
                return []
        
        if self.gemini_model is None:
            # gemini-2.0-flashを固定値として使用（モデル検索を避けるため、直接モデル名を指定）
            try:
                # モデル名を明示的に指定（models/プレフィックス付き、位置引数で指定）
                self.gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
                self.gemini_model_name = 'gemini-2.0-flash'
                log_info("Geminiクライアントを初期化しました: gemini-2.0-flash")
            except Exception as e:
                log_error(f"Geminiモデル（gemini-2.0-flash）の初期化に失敗: {str(e)}")
                return []
        
        try:
            # numpy配列をPIL画像に変換（画像は既にRGB形式であると仮定）
            # PILで読み込んだ画像は常にRGB形式なので、そのまま使用
            pil_image = Image.fromarray(image)
            
            # Geminiに送信するプロンプト
            prompt = """あなたは高精度な日本語OCRアシスタントです。
画像内のテキストを以下の制約に従って抽出してください:
– 文字の配置や段落構造を維持する。
– 数字、記号、特殊文字も正確に認識する。
– 文脈を考慮して誤認識を修正する。
– 一文の途中の改行は削除する。
– 住所の場合は都道府県名を含む完全な住所として抽出する（例：「県○○市...」ではなく「新潟県○○市...」のように）。

画像内のすべてのテキストを抽出してください。"""
            
            # 画像をPNGバイトへ変換
            import io
            buf = io.BytesIO()
            pil_image.save(buf, format='PNG')
            image_bytes = buf.getvalue()
            # Gemini APIを呼び出し（マルチパート）
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_bytes}
            ])
            
            if response and response.text:
                # テキストを行ごとに分割
                lines = response.text.strip().split('\n')
                
                results = []
                for line in lines:
                    line = line.strip()
                    if line:
                        results.append({
                            'text': line,
                            'confidence': 95.0,  # Geminiは高精度と仮定
                            'method': 'gemini'
                        })
                
                # ログを簡略化（詳細は非表示）
                return results
            else:
                log_warning("Gemini OCRでテキストを抽出できませんでした")
                return []
                
        except Exception as e:
            error_message = str(e)
            
            # クォータ制限エラーの場合
            if "quota" in error_message.lower() or "429" in error_message:
                log_error("Gemini APIのクォータ制限に達しています。しばらく待ってから再試行してください。")
            # その他のエラー
            else:
                log_error(f"Gemini OCR処理でエラーが発生しました: {error_message}")
            return []
    
    def _complete_prefecture_name(self, address: str) -> str:
        """
        不完全な都道府県名を補完する
        
        Args:
            address: 不完全な住所（例：「県長岡市...」）
            
        Returns:
            補完された住所（例：「新潟県長岡市...」）
        """
        # 都道府県名が欠けている可能性があるパターンをチェック
        # 「県○○市」「府○○市」「都○○市」「道○○市」で始まる場合
        prefix_pattern = r'^([都道府県])([^都道府県\s]+)'
        match = re.match(prefix_pattern, address)
        
        if match:
            prefix = match.group(1)  # 「県」「府」「都」「道」
            rest = match.group(2)    # 残りの部分
            
            # 市区町村名から都道府県を推測するマッピング
            city_to_prefecture = {
                '長岡市': '新潟県',
                '新潟市': '新潟県',
                '上越市': '新潟県',
                '三条市': '新潟県',
                '柏崎市': '新潟県',
                '新発田市': '新潟県',
                '小千谷市': '新潟県',
                '加茂市': '新潟県',
                '十日町市': '新潟県',
                '見附市': '新潟県',
                '村上市': '新潟県',
                '燕市': '新潟県',
                '糸魚川市': '新潟県',
                '妙高市': '新潟県',
                '五泉市': '新潟県',
                '阿賀野市': '新潟県',
                '佐渡市': '新潟県',
                '魚沼市': '新潟県',
                '南魚沼市': '新潟県',
                '胎内市': '新潟県',
            }
            
            # 市区町村名を抽出（最初の市区町村まで）
            # 「市」「区」「町」「村」で終わる文字列を検索
            city_match = re.search(r'(.+?[市区町村])', rest)
            if city_match:
                city_name = city_match.group(1)
                if city_name in city_to_prefecture:
                    # 都道府県名を補完
                    prefecture = city_to_prefecture[city_name]
                    # 「県長岡市...」→「新潟県長岡市...」に置換
                    return prefecture + rest
        
        return address
    
    def extract_addresses_from_text(self, text: str) -> List[str]:
        """
        テキストから住所を抽出（大幅改善版）
        
        Args:
            text: 入力テキスト
            
        Returns:
            抽出された住所のリスト
        """
        addresses = []
        location_addresses = set()  # 「物件所在地」から抽出された住所を記録
        
        # まず「物件所在地」から直接抽出（最優先）
        location_pattern = r'物件所在地\s*([^\n]+?)(?=\s*交通|\s*建物|$)'
        location_matches = re.findall(location_pattern, text, re.MULTILINE | re.DOTALL)
        for match in location_matches:
            match = match.strip()
            if match:
                # 物件所在地から抽出された場合は検証を緩和
                is_valid = self.is_valid_address(match)
                if not is_valid:
                    # さらに緩和した検証（物件所在地の場合は特別扱い）
                    has_pref = bool(re.search(r'[都道府県]', match))
                    has_city = bool(re.search(r'[市区町村]', match))
                    has_number = bool(re.search(r'[0-9]', match))
                    if has_pref and has_city and has_number:
                        addresses.append(match)
                        location_addresses.add(match)
                else:
                    addresses.append(match)
                    location_addresses.add(match)
        
        # 完全な住所パターンを優先的に抽出
        # 都道府県 + 市区町村 + 町名 + 丁目 + 番地の形式
        full_address_pattern = r'([都道府県][^都道府県\s]*?[市区町村][^市区町村\s]*?[町字][^町字\s]*?[0-9]+[丁目]*\s*[0-9\-]+)'
        full_matches = re.findall(full_address_pattern, text)
        for match in full_matches:
            match = match.strip()
            if match and self.is_valid_address(match) and match not in addresses:
                addresses.append(match)
        
        # その他のパターンで抽出
        for i, pattern in enumerate(self.address_patterns):
            # 既に「物件所在地」パターンは処理済みなのでスキップ
            if '物件所在地' in pattern:
                continue
                
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                match = match.strip()
                
                # 既に抽出されている完全な住所の一部でないかチェック
                is_partial = False
                for existing in addresses:
                    if match in existing or existing in match:
                        if len(match) < len(existing):
                            is_partial = True
                            break
                
                if not is_partial:
                    # 住所らしさをチェック
                    if self.is_valid_address(match):
                        addresses.append(match)
        
        # 不完全な都道府県名を補完
        completed_addresses = []
        for addr in addresses:
            # 「県」「府」「都」「道」で始まる住所（都道府県名が不完全な可能性がある）
            if (addr.startswith('県') or addr.startswith('府') or 
                addr.startswith('都') or addr.startswith('道')):
                # 都道府県名が含まれているかチェック（「新潟県」のように完全な都道府県名）
                if not re.search(r'^[^\s]{2,}[都道府県]', addr):
                    # 都道府県名が不完全な可能性があるので補完を試行
                    completed_addr = self._complete_prefecture_name(addr)
                    completed_addresses.append(completed_addr)
                else:
                    completed_addresses.append(addr)
            else:
                completed_addresses.append(addr)
        
        # 完全な住所のみを抽出（不完全な住所を除外）
        final_addresses = []
        for addr in completed_addresses:
            # 「県」や「市」から始まる不完全な住所を除外
            # ただし、都道府県名が含まれている場合は除外しない
            if (addr.startswith('県') or addr.startswith('府') or addr.startswith('都') or addr.startswith('道')):
                # 都道府県名が含まれているかチェック（最初の10文字内）
                if not re.search(r'^[^\s]*[都道府県]', addr[:15]):
                    # 都道府県名が完全でない場合は補完を試行
                    addr = self._complete_prefecture_name(addr)
                    # それでも不完全な場合はスキップ
                    if addr.startswith('県') or addr.startswith('府') or addr.startswith('都') or addr.startswith('道'):
                        if not re.search(r'^[^\s]*[都道府県]', addr[:15]):
                            continue
            
            # 完全な住所のパターンをチェック（緩和）
            # 都道府県名 + 市区町村 + 数字 があればOK
            has_full_pattern = re.search(r'^[^\s]*[都道府県].*[市区町村].*[0-9]', addr)
            if has_full_pattern:
                final_addresses.append(addr)
        
        # 重複を除去（完全な住所のみ）
        unique_addresses = []
        seen = set()
        for addr in final_addresses:
            if addr not in seen:
                unique_addresses.append(addr)
                seen.add(addr)
        
        # 最も信頼性の高い住所を1つだけ選択
        if len(unique_addresses) > 0:
            # 優先順位でソート
            sorted_addresses = []
            for addr in unique_addresses:
                score = 0
                # 「物件所在地」から抽出された場合は最優先
                if addr in location_addresses:
                    score += 1000
                # 長い住所を優先（より詳細な情報を含む）
                score += len(addr)
                # 完全な住所パターン（都道府県 + 市区町村 + 町名 + 番地）を優先
                if re.search(r'[都道府県].*[市区町村].*[町字].*[0-9]', addr):
                    score += 500
                # 番地（数字-数字の形式）を含む場合はさらに優先
                if re.search(r'[0-9]+\s*[-－]\s*[0-9]+', addr):
                    score += 100
                sorted_addresses.append((score, addr))
            
            # スコアが高い順にソート
            sorted_addresses.sort(key=lambda x: x[0], reverse=True)
            
            # 最高スコアの住所を1つだけ返す
            best_address = sorted_addresses[0][1]
            
            return [best_address]
        else:
            return []
    
    def is_valid_address(self, text: str) -> bool:
        """
        テキストが有効な住所かどうかを判定（厳密版 - 完全な住所のみ）
        
        Args:
            text: 判定するテキスト
            
        Returns:
            有効な住所の場合True
        """
        # 最小長チェック
        if len(text) < 5:
            return False
        
        # 都道府県名が含まれているかチェック
        prefectures = ['都', '道', '府', '県']
        has_prefecture = any(p in text for p in prefectures)
        
        # 都道府県名の前に都道府県名があるか（「新潟県」のように完全な都道府県名）
        # 「県」だけでなく、都道府県名全体が含まれていることを確認
        prefecture_pattern = r'[^\s都道府県]*[都道府県]'
        has_full_prefecture = bool(re.search(prefecture_pattern, text))
        
        # 市区町村名が含まれているかチェック
        municipalities = ['市', '区', '町', '村']
        has_municipality = any(m in text for m in municipalities)
        
        # 数字が含まれているかチェック（番地）
        has_number = bool(re.search(r'[0-9]', text))
        
        # 住所らしき文字が含まれているかチェック
        address_chars = ['町', '字', '丁目', '番地', '号']
        has_address_chars = any(c in text for c in address_chars)
        
        # 不完全な住所のパターンをチェック（除外する）
        # 「県」や「市」から始まる住所は除外（ただし都道府県名が前にない場合のみ）
        if (text.startswith('県') or text.startswith('市')) and not re.search(r'[都道府県]', text[:10]):
            return False
        
        # 判定条件（完全な住所を優先）
        # 1. 完全な都道府県名 + 市区町村 + (町名 + 数字または番地)
        condition1 = (has_full_prefecture or has_prefecture) and has_municipality and (has_address_chars or has_number)
        
        # 2. 都道府県 + 市区町村 + 数字（丁目などの文字がなくても、番地があればOK）
        condition2 = has_prefecture and has_municipality and has_number
        
        return condition1 or condition2
    
    def extract_from_image(self, image_path: str) -> Dict:
        """
        画像から住所を抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            抽出結果の辞書
        """
        # 変数を初期化
        quota_exceeded = False
        
        try:
            # ファイルサイズチェック
            file_size = os.path.getsize(image_path)
            if not validate_file_size(file_size):
                return {
                    'success': False,
                    'error': 'ファイルサイズが大きすぎます',
                    'addresses': []
                }
            
            # 画像読み込み（PILを使用）
            try:
                # PILで画像を読み込み（RGB形式）
                pil_image = Image.open(image_path)
                # RGBAの場合はRGBに変換
                if pil_image.mode == 'RGBA':
                    # 白背景に合成してRGBに変換
                    rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                    rgb_image.paste(pil_image, mask=pil_image.split()[3] if len(pil_image.split()) == 4 else None)
                    pil_image = rgb_image
                elif pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                # PIL画像をnumpy配列に変換（RGB形式のまま）
                image = np.array(pil_image)
            except Exception as e:
                log_error(f"画像の読み込みに失敗しました: {str(e)}")
                return {
                    'success': False,
                    'error': f'画像の読み込みに失敗しました: {str(e)}',
                    'addresses': []
                }
            if image is None:
                return {
                    'success': False,
                    'error': '画像の読み込みに失敗しました',
                    'addresses': []
                }
            
            log_info("OCR処理を開始しています...")
            
            # Geminiのみ使用
            if not self.gemini_available:
                return {
                    'success': False,
                    'error': f"Geminiが利用できません: {getattr(self, 'gemini_init_error', '初期化失敗')}",
                    'addresses': []
                }
            
            log_info("GeminiでOCRを実行します")
            gemini_results = self.extract_text_gemini(image)
            if not gemini_results:
                return {
                    'success': False,
                    'error': 'Gemini OCRでテキストを抽出できませんでした',
                    'addresses': []
                }
            all_texts = [r['text'] for r in gemini_results]
            
            # 従来の住所抽出
            addresses = []
            for text in all_texts:
                extracted_addresses = self.extract_addresses_from_text(text)
                addresses.extend(extracted_addresses)
            
            # 重複を除去
            unique_addresses = list(set(addresses))
            
            # OpenAI補完は使用しない（Geminiのみ使用）
            ai_addresses = []
            ai_response = ""
            
            # 結果を統合（従来の住所抽出のみ）
            all_addresses = list(set(unique_addresses))
            
            # 最も信頼性の高い住所を1つだけ選択
            if all_addresses:
                # 優先順位でソート（最長の住所を優先、その後は完全な住所パターンを優先）
                sorted_addresses = []
                for addr in all_addresses:
                    score = 0
                    # 長い住所を優先（より詳細な情報を含む）
                    score += len(addr)
                    # 完全な住所パターン（都道府県 + 市区町村 + 町名 + 番地）を優先
                    if re.search(r'[都道府県].*[市区町村].*[町字].*[0-9]', addr):
                        score += 500
                    # 番地（数字-数字の形式）を含む場合はさらに優先
                    if re.search(r'[0-9]+\s*[-－]\s*[0-9]+', addr):
                        score += 100
                    sorted_addresses.append((score, addr))
                
                # スコアが高い順にソート
                sorted_addresses.sort(key=lambda x: x[0], reverse=True)
                best_address = sorted_addresses[0][1]
                
                return {
                    'success': True,
                    'addresses': [best_address],
                    'raw_texts': all_texts,
                    'ai_response': ai_response,
                    'traditional_addresses': unique_addresses,
                    'ai_addresses': ai_addresses,
                    'quota_exceeded': quota_exceeded
                }
            else:
                # 住所が抽出できなかった場合の詳細情報
                error_detail = '住所を抽出できませんでした'
                if not all_texts:
                    error_detail += '（画像からテキストが抽出できませんでした）'
                elif len(all_texts) > 0:
                    # テキストは抽出できたが住所として認識できなかった
                    error_detail += f'（抽出されたテキスト: {len(all_texts)}行）'
                    # 住所らしき部分があるか確認
                    address_like_texts = []
                    for text in all_texts:
                        if any(keyword in text for keyword in ['物件', '所在地', '都', '県', '市', '区', '町', '村', '丁目', '番地']):
                            address_like_texts.append(text)
                    if address_like_texts:
                        error_detail += f'（住所らしきテキストを{len(address_like_texts)}件発見）'
                
                return {
                    'success': False,
                    'error': error_detail,
                    'addresses': [],
                    'raw_texts': all_texts,
                    'ai_response': ai_response,
                    'quota_exceeded': quota_exceeded,
                    'address_candidates': unique_addresses if 'unique_addresses' in locals() else []
                }
                
        except Exception as e:
            log_error(f"住所抽出処理でエラーが発生しました: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'addresses': [],
                'quota_exceeded': False
            }
    
    def extract_from_pil_image(self, pil_image: Image.Image) -> Dict:
        """
        PIL画像から住所を抽出
        
        Args:
            pil_image: PIL画像オブジェクト
            
        Returns:
            抽出結果の辞書
        """
        # 変数を初期化
        quota_exceeded = False
        
        try:
            # PIL画像をnumpy配列に変換（RGB形式のまま）
            # RGBAの場合はRGBに変換
            if pil_image.mode == 'RGBA':
                # 白背景に合成してRGBに変換
                rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[3] if len(pil_image.split()) == 4 else None)
                pil_image = rgb_image
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            # PIL画像をnumpy配列に変換（RGB形式）
            image = np.array(pil_image)
            
            log_info("OCR処理を開始しています...")
            
            # Geminiのみ使用
            if not self.gemini_available:
                return {
                    'success': False,
                    'error': f"Geminiが利用できません: {getattr(self, 'gemini_init_error', '初期化失敗')}",
                    'addresses': []
                }
            
            log_info("GeminiでOCRを実行します")
            gemini_results = self.extract_text_gemini(image)
            if not gemini_results:
                return {
                    'success': False,
                    'error': 'Gemini OCRでテキストを抽出できませんでした',
                    'addresses': []
                }
            all_texts = [r['text'] for r in gemini_results]
            
            # 従来の住所抽出
            addresses = []
            for text in all_texts:
                extracted_addresses = self.extract_addresses_from_text(text)
                addresses.extend(extracted_addresses)
            
            # 重複を除去
            unique_addresses = list(set(addresses))
            
            # OpenAI補完は使用しない（Geminiのみ使用）
            ai_addresses = []
            ai_response = ""
            
            # 結果を統合（従来の住所抽出のみ）
            all_addresses = list(set(unique_addresses))
            
            # 最も信頼性の高い住所を1つだけ選択
            if all_addresses:
                # 優先順位でソート（最長の住所を優先、その後は完全な住所パターンを優先）
                sorted_addresses = []
                for addr in all_addresses:
                    score = 0
                    # 長い住所を優先（より詳細な情報を含む）
                    score += len(addr)
                    # 完全な住所パターン（都道府県 + 市区町村 + 町名 + 番地）を優先
                    if re.search(r'[都道府県].*[市区町村].*[町字].*[0-9]', addr):
                        score += 500
                    # 番地（数字-数字の形式）を含む場合はさらに優先
                    if re.search(r'[0-9]+\s*[-－]\s*[0-9]+', addr):
                        score += 100
                    sorted_addresses.append((score, addr))
                
                # スコアが高い順にソート
                sorted_addresses.sort(key=lambda x: x[0], reverse=True)
                best_address = sorted_addresses[0][1]
                
                return {
                    'success': True,
                    'addresses': [best_address],
                    'raw_texts': all_texts,
                    'ai_response': ai_response,
                    'traditional_addresses': unique_addresses,
                    'ai_addresses': ai_addresses,
                    'quota_exceeded': quota_exceeded
                }
            else:
                # 住所が抽出できなかった場合の詳細情報
                error_detail = '住所を抽出できませんでした'
                if not all_texts:
                    error_detail += '（画像からテキストが抽出できませんでした）'
                elif len(all_texts) > 0:
                    # テキストは抽出できたが住所として認識できなかった
                    error_detail += f'（抽出されたテキスト: {len(all_texts)}行）'
                    # 住所らしき部分があるか確認
                    address_like_texts = []
                    for text in all_texts:
                        if any(keyword in text for keyword in ['物件', '所在地', '都', '県', '市', '区', '町', '村', '丁目', '番地']):
                            address_like_texts.append(text)
                    if address_like_texts:
                        error_detail += f'（住所らしきテキストを{len(address_like_texts)}件発見）'
                
                return {
                    'success': False,
                    'error': error_detail,
                    'addresses': [],
                    'raw_texts': all_texts,
                    'ai_response': ai_response,
                    'quota_exceeded': quota_exceeded,
                    'address_candidates': unique_addresses if 'unique_addresses' in locals() else []
                }
                
        except Exception as e:
            log_error(f"住所抽出処理でエラーが発生しました: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'addresses': [],
                'quota_exceeded': False
            }


def create_ocr_extractor(tesseract_cmd: str = "", ocr_mode: str = "gemini", openai_api_key: str = "", gemini_api_key: str = "") -> OCRAddressExtractor:
    """
    OCR住所抽出器を作成する（Geminiのみ使用）
    
    Args:
        tesseract_cmd: （使用しない、互換性のため残す）
        ocr_mode: （常に"gemini"）
        openai_api_key: （使用しない、互換性のため残す）
        gemini_api_key: Gemini APIキー
        
    Returns:
        OCRAddressExtractorインスタンス
    """
    return OCRAddressExtractor(tesseract_cmd, ocr_mode, openai_api_key, gemini_api_key)
