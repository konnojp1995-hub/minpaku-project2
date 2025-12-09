"""
法令判定モジュール
Geminiを使用して物件情報の抽出と法令判定を行う機能を提供
"""
import json
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .utils import log_error, log_info, load_rules

# Google Geminiのインポート
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    # インポート時はログを出力しない（初期化時に適切なエラーメッセージを表示）


class LawChecker:
    """法令に基づく適法性を判定するクラス（Gemini使用）"""
    
    def __init__(self, rules_file: str = "rules.json", gemini_api_key: str = ""):
        """
        初期化
        
        Args:
            rules_file: ルールファイルのパス
            gemini_api_key: Gemini APIキー
        """
        self.rules_file = rules_file
        self.rules = load_rules()
        self.gemini_api_key = gemini_api_key
        self.gemini_init_error = ""
        
        # Geminiクライアントを初期化
        if not GEMINI_AVAILABLE:
            self.gemini_available = False
            self.gemini_init_error = "google-generativeaiライブラリがインストールされていません。'pip install google-generativeai' でインストールしてください。"
        elif not gemini_api_key:
            self.gemini_available = False
            self.gemini_init_error = "Gemini APIキーが未設定です。サイドバーで設定してください。"
        else:
            self.gemini_available = True
            # genai.configure()とモデルの初期化は完全に遅延させる（実際にAPIを使用する時まで待つ）
            # 起動時の不要なAPIコールを完全に避けるため、すべての初期化を遅延
            self.gemini_api_key = gemini_api_key
            self.gemini_model = None
            self.gemini_model_name = None  # 使用するモデル名（遅延初期化時に決定）
            self.gemini_init_error = ""
            self._gemini_configured = False  # configure()が呼ばれたかどうか
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Gemini APIを呼び出す
        
        Args:
            prompt: プロンプト
            
        Returns:
            Geminiからの応答
        """
        if not self.gemini_available:
            return "Gemini APIが利用できません"
        
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
                return f"エラー: {self.gemini_init_error}"
        
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
                    return f"エラー: {self.gemini_init_error}"
                self.gemini_available = False
                self.gemini_init_error = f"Geminiモデル（gemini-2.0-flash）の初期化に失敗: {error_str}"
                log_error(self.gemini_init_error)
                return f"エラー: {self.gemini_init_error}"
        
        try:
            # 429エラーが既に発生している場合は即座にエラーを返す
            if not self.gemini_available:
                return f"エラー: {self.gemini_init_error}"
            
            response = self.gemini_model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            return "応答を取得できませんでした"
        except Exception as e:
            error_str = str(e)
            # 429エラー（クォータ超過）の場合は即座に停止し、後続の呼び出しを防ぐ
            if "429" in error_str or "quota" in error_str.lower():
                self.gemini_available = False
                self.gemini_init_error = "Gemini APIのクォータ制限に達しています。しばらく待ってから再試行してください。"
                log_error(self.gemini_init_error)
                return f"エラー: {self.gemini_init_error}"
            log_error(f"Gemini API呼び出しエラー: {error_str}")
            return f"エラー: {error_str}"
    
    def extract_property_info(self, extracted_text: str) -> Dict:
        """
        抽出されたテキストから物件情報を抽出
        
        Args:
            extracted_text: OCRで抽出されたテキスト
            
        Returns:
            物件情報の辞書
        """
        prompt = f"""以下の不動産広告のテキストから、以下の項目を抽出してJSON形式で返してください。
各項目が見つからない場合は、該当する項目を省略してください。

抽出テキスト:
{extracted_text}

抽出項目:
- 所在地: 物件の住所または所在地
- 建物用途: 戸建て、マンション、アパートのいずれか（省略可）
- 構造: 木造、鉄骨造、RC造（鉄筋コンクリート造）、SRC造（鉄骨鉄筋コンクリート造）のいずれか（省略可）
- 階数: 例「2階建」「3階建て」「5階建て」などの形式（省略可）
- 延べ床面積: 民泊で使用予定の部屋の延べ床面積（数値のみ、単位なし、省略可）

JSON形式で、以下の構造で返してください:
{{
  "所在地": "住所",
  "建物用途": "戸建て|マンション|アパート",
  "構造": "木造|鉄骨造|RC造|SRC造",
  "階数": "階数表記（例：2階建）",
  "延べ床面積": "面積（数値のみ、単位なし）"
}}

不明な項目は省略してください。JSONのみを返してください。"""
        
        response_text = self._call_gemini(prompt)
        
        # JSONを抽出
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                property_info = json.loads(json_match.group())
            else:
                property_info = {}
        except:
            property_info = {}
        
        return {
            'success': True,
            'property_info': property_info,
            'raw_response': response_text
        }
    
    def check_minpaku_permission(self, zoning_type: str, address: str) -> Dict:
        """
        民泊新法の許可判定
        
        Args:
            zoning_type: 用途地域
            address: 物件の住所
            
        Returns:
            判定結果
        """
        prompt = f"""物件情報に基づいて、民泊新法（住宅宿泊事業法）の許可可能性を簡潔に判定してください。

物件情報:
- 用途地域: {zoning_type}
- 所在地: {address}

以下の形式で厳密に回答してください（各項目は1行で簡潔に）:

許可判定: [許可 / 不許可]
主な理由: [用途地域や条例に基づく簡潔な説明を1行で]
その他制限: [自治体独自の制限がある場合のみ記載、なければ「特になし」]

例:
許可判定: 許可
主な理由: 住居専用地域だが条例制限なし
その他制限: 年間180日制限あり"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'permission': response,
            'raw_response': response
        }
    
    def check_ryokan_permission(self, zoning_type: str, address: str) -> Dict:
        """
        旅館業の許可判定
        
        Args:
            zoning_type: 用途地域
            address: 物件の住所
            
        Returns:
            判定結果
        """
        prompt = f"""物件情報に基づいて、旅館業法の許可可能性を簡潔に判定してください。

物件情報:
- 用途地域: {zoning_type}
- 所在地: {address}

以下の形式で厳密に回答してください（各項目は1行で簡潔に）:

許可判定: [許可 / 不許可 / 条件付き許可]
主な理由: [条例・立地要件などを簡潔に1行で記載]
その他制限: [特記事項のみ、なければ「特になし」]

例:
許可判定: 条件付き許可
主な理由: 学校から100m以内の場合制限あり
その他制限: 特になし"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'permission': response,
            'raw_response': response
        }
    
    def check_tokku_minpaku_permission(self, zoning_type: str, address: str) -> Dict:
        """
        特区民泊の許可判定
        
        Args:
            zoning_type: 用途地域
            address: 物件の住所
            
        Returns:
            判定結果
        """
        prompt = f"""物件情報に基づいて、特区民泊（国家戦略特別区域法に基づく民泊）の許可可能性を簡潔に判定してください。

物件情報:
- 用途地域: {zoning_type}
- 所在地: {address}

まず、{address}の市区町村で特区民泊が認められているかを確認してください。
次に、用途地域の情報を用いて許可可能性を判定してください。

以下の形式で厳密に回答してください（各項目は1行で簡潔に）:

許可判定: [許可 / 不許可]
主な理由: [特区指定の有無など簡潔に1行で]
その他制限: [該当自治体の特例がある場合のみ、なければ「特になし」]

例:
許可判定: 不許可
主な理由: 特区指定外エリア
その他制限: 特になし"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'permission': response,
            'raw_response': response
        }
    
    def check_fire_law_requirements(self, building_use: str, structure: str, floors: str, floor_area: str) -> Dict:
        """
        消防法上のポイントを調査
        
        Args:
            building_use: 建物用途
            structure: 構造
            floors: 階数
            floor_area: 延べ床面積
            
        Returns:
            消防法上の要件
        """
        prompt = f"""以下の建物情報に基づいて、消防法上の必要な設備・要件を簡潔に調査してください。

建物情報:
- 用途: {building_use}
- 構造: {structure}
- 階数: {floors}
- 延べ床面積: {floor_area}㎡（民泊で使用予定の部屋）

以下の形式で厳密に回答してください（各項目は1行で簡潔に）:

火災報知器: [必要設備を簡潔に1行で]
竪穴区画: [要 / 不要 と理由を1行で]
その他留意点: [消火器・誘導灯・防炎物品など主要義務のみ簡潔に1行で]

例:
火災報知器: 住宅用火災警報器で可
竪穴区画: 不要（2階建・延べ150㎡のため）
その他留意点: 消火器設置義務あり"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'requirements': response,
            'raw_response': response
        }
    
    def check_building_standards_requirements(self, building_use: str, structure: str, floors: str, floor_area: str) -> Dict:
        """
        建築基準法上のポイントを調査
        
        Args:
            building_use: 建物用途
            structure: 構造
            floors: 階数
            floor_area: 延べ床面積
            
        Returns:
            建築基準法上の要件
        """
        prompt = f"""以下の建物情報に基づいて、建築基準法上の必要な要件を簡潔に調査してください。

建物情報:
- 用途: {building_use}
- 構造: {structure}
- 階数: {floors}
- 延べ床面積: {floor_area}㎡（民泊で使用予定の部屋）

以下の形式で厳密に回答してください（各項目は1行で簡潔に）:

用途変更: [要 / 不要 と理由を1行で]
竪穴区画: [要 / 不要 と理由を1行で]
その他制限: [主要な注意点を簡潔に1行で]
接道義務: [該当有無と簡潔な説明を1行で]

例:
用途変更: 不要（200㎡未満）
竪穴区画: 不要
接道義務: 旅館業を申請する場合、幅員4m以上の道路に2m以上接する義務あり
その他制限: 採光・換気要件あり"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'requirements': response,
            'raw_response': response
        }
    
    def check_local_restrictions(self, address: str) -> Dict:
        """
        市区町村の制限を調査
        
        Args:
            address: 物件の住所
            
        Returns:
            市区町村の制限事項
        """
        prompt = f"""{address}の市区町村で、民泊運営に関して独自の規制や注意点があるか調査してください。

自治体独自の規制や注意点がある場合のみ簡潔に記載してください。
制限事項がなければ「特になし」と記載してください。

回答は1行で簡潔に記載してください。"""
        
        response = self._call_gemini(prompt)
        
        return {
            'success': True,
            'restrictions': response,
            'raw_response': response
        }


def create_law_checker(rules_file: str = "rules.json", gemini_api_key: str = "") -> LawChecker:
    """
    法令チェッカーを作成する
    
    Args:
        rules_file: ルールファイルのパス
        gemini_api_key: Gemini APIキー
        
    Returns:
        LawCheckerインスタンス
    """
    return LawChecker(rules_file, gemini_api_key)
