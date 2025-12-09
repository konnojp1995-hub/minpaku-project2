"""
初期費用推定モジュール
OCRテキストやGeminiを使用して初期費用を推定する
"""
import re
import json
from typing import Dict, Optional
from .utils import log_info, log_error, log_warning
from .law_checker import LawChecker


class InitialCostEstimator:
    """初期費用を推定するクラス"""
    
    def __init__(self, gemini_api_key: str = ""):
        """
        初期化
        
        Args:
            gemini_api_key: Gemini APIキー
        """
        self.gemini_api_key = gemini_api_key
        self.law_checker = None
        
        if gemini_api_key:
            try:
                self.law_checker = LawChecker(gemini_api_key=gemini_api_key)
            except Exception as e:
                log_error(f"LawCheckerの初期化に失敗: {str(e)}")

    def _parse_cost_value(self, raw_value, rent_value: int = 0) -> int:
        """
        金額または「●ヶ月」表記を数値に変換
        
        Args:
            raw_value: 金額または「●ヶ月」表記（文字列または数値）
            rent_value: 月額家賃（「●ヶ月」表記の場合に使用）
        
        Returns:
            整数の金額（変換できない場合は0）
        """
        if raw_value is None:
            return 0
        try:
            value_str = str(raw_value).strip()
            # 「なし」「無し」「0円」などは0扱い
            if value_str in ["なし", "無し", "0", "0円", "なし。", "無し。"]:
                return 0
            # すでに数値の場合
            if isinstance(raw_value, (int, float)):
                return int(raw_value)
            # 例: "2ヶ月", "1.5か月", "3ヵ月", "2月分"
            month_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*[ヶ月か月ヵ月月分]', value_str)
            if month_match and rent_value > 0:
                months = float(month_match.group(1))
                return int(round(months * rent_value))
            # 数値のみ
            digits_match = re.search(r'[0-9,]+', value_str)
            if digits_match:
                return int(digits_match.group().replace(',', ''))
        except Exception:
            pass
        return 0
    
    def extract_initial_costs_from_ocr(self, extracted_text: str) -> Dict:
        """
        OCRテキストから初期費用項目を抽出
        
        Args:
            extracted_text: OCRで抽出されたテキスト
            
        Returns:
            初期費用項目の辞書
        """
        if not extracted_text:
            return {
                'deposit': 0,           # 敷金
                'key_money': 0,         # 礼金
                'brokerage_fee': 0,     # 仲介手数料
                'guarantee_company': 0, # 保証会社
                'fire_insurance': 0     # 火災保険
            }
        
        # Geminiを使ってOCRテキストから初期費用を抽出
        rent_value = 0
        try:
            rent_data = self.extract_rent_from_ocr(extracted_text)
            # 家賃と管理費を合算（家賃が0でも管理費があれば加算）
            rent_value = (rent_data.get('rent', 0) or 0) + (rent_data.get('management_fee', 0) or 0)
        except Exception:
            rent_value = 0

        if self.law_checker and self.law_checker.gemini_available:
            prompt = f"""以下の不動産広告のテキストから、初期費用に関する項目を抽出し、必ず金額（円）で返してください。
月数や割合で書かれている場合は、賃料（推定: {rent_value}円/月）を用いて金額に変換してください。
（例: 敷金2ヶ月 → {rent_value}×2、礼金1ヶ月 → {rent_value}×1、仲介手数料1.1ヶ月 → {rent_value}×1.1、初回保証料:月額総賃料50% → {rent_value}×0.5）
「なし/無し/0円」は0としてください。数値のみを返してください。

抽出テキスト:
{extracted_text}

抽出項目:
- 敷金: 敷金の金額（円）。月数表記なら賃料×月数。なければ0。
- 礼金: 礼金の金額（円）。月数表記なら賃料×月数。なければ0。
- 仲介手数料: 仲介手数料の金額（円）。月数表記なら賃料×月数。なければ0。
- 保証会社: 保証会社の初回保証料の金額（円）。「月額総賃料50%」など割合なら賃料×割合で計算。なければ0。
- 火災保険: 火災保険の金額（円）。なければ0。

JSON形式で、以下の構造で返してください:
{{
  "敷金": 0,
  "礼金": 0,
  "仲介手数料": 0,
  "保証会社": 0,
  "火災保険": 0
}}

数値のみを返してください。JSONのみを返してください。"""
            
            try:
                response_text = self.law_checker._call_gemini(prompt)
                
                # JSONを抽出
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    cost_data = json.loads(json_match.group())
                    return {
                        'deposit': self._parse_cost_value(cost_data.get('敷金', 0), rent_value),
                        'key_money': self._parse_cost_value(cost_data.get('礼金', 0), rent_value),
                        'brokerage_fee': self._parse_cost_value(cost_data.get('仲介手数料', 0), rent_value),
                        'guarantee_company': self._parse_cost_value(cost_data.get('保証会社', 0), rent_value),
                        'fire_insurance': self._parse_cost_value(cost_data.get('火災保険', 0), rent_value)
                    }
            except Exception as e:
                log_error(f"OCRテキストからの初期費用抽出エラー: {str(e)}")
        
        # フォールバック: 正規表現で抽出を試みる
        return self._extract_costs_with_regex(extracted_text, rent_value)
    
    def _extract_costs_with_regex(self, text: str, rent_value: int = 0) -> Dict:
        """
        正規表現を使って初期費用を抽出（フォールバック）
        
        Args:
            text: OCRテキスト
            
        Returns:
            初期費用項目の辞書
        """
        result = {
            'deposit': 0,
            'key_money': 0,
            'brokerage_fee': 0,
            'guarantee_company': 0,
            'fire_insurance': 0
        }
        
        # 敷金のパターン
        deposit_patterns = [
            r'敷金[：:]\s*([0-9,]+)',
            r'敷[：:]\s*([0-9,]+)',
            r'敷金\s*([0-9,]+)'
        ]
        for pattern in deposit_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['deposit'] = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        if result['deposit'] == 0 and rent_value > 0:
            month_match = re.search(r'敷金[：:\s]*([0-9]+(?:\.[0-9]+)?)\s*[ヶ月か月ヵ月月分]', text)
            if month_match:
                try:
                    months = float(month_match.group(1))
                    result['deposit'] = int(round(months * rent_value))
                except:
                    pass
        
        # 礼金のパターン
        key_money_patterns = [
            r'礼金[：:]\s*([0-9,]+)',
            r'礼[：:]\s*([0-9,]+)',
            r'礼金\s*([0-9,]+)'
        ]
        for pattern in key_money_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['key_money'] = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        if result['key_money'] == 0 and rent_value > 0:
            month_match = re.search(r'礼金[：:\s]*([0-9]+(?:\.[0-9]+)?)\s*[ヶ月か月ヵ月月分]', text)
            if month_match:
                try:
                    months = float(month_match.group(1))
                    result['key_money'] = int(round(months * rent_value))
                except:
                    pass
        
        # 仲介手数料のパターン
        brokerage_patterns = [
            r'仲介[手数料]*[：:]\s*([0-9,]+)',
            r'仲介手数料\s*([0-9,]+)'
        ]
        for pattern in brokerage_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['brokerage_fee'] = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        if result['brokerage_fee'] == 0 and rent_value > 0:
            month_match = re.search(r'仲介[手数料]*[：:\s]*([0-9]+(?:\.[0-9]+)?)\s*[ヶ月か月ヵ月月分]', text)
            if month_match:
                try:
                    months = float(month_match.group(1))
                    result['brokerage_fee'] = int(round(months * rent_value))
                except:
                    pass
        
        # 保証会社 / 保証金のパターン
        guarantee_patterns = [
            r'保証[会社]*[：:]\s*([0-9,]+)',
            r'保証会社\s*([0-9,]+)',
            r'保証金[：:]\s*([0-9,]+)'
        ]
        for pattern in guarantee_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['guarantee_company'] = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        if result['guarantee_company'] == 0 and rent_value > 0:
            month_match = re.search(r'保証(会社|金)?[：:\s]*([0-9]+(?:\.[0-9]+)?)\s*[ヶ月か月ヵ月月分]', text)
            if month_match:
                try:
                    months = float(month_match.group(2))
                    result['guarantee_company'] = int(round(months * rent_value))
                except:
                    pass
        # 「初回保証料:月額総賃料50%」などの割合指定
        if result['guarantee_company'] == 0 and rent_value > 0:
            percent_match = re.search(r'初回保証料[:：]?\s*月額総賃料\s*([0-9]+)\s*%?', text)
            if percent_match:
                try:
                    pct = float(percent_match.group(1))
                    result['guarantee_company'] = int(round(rent_value * pct / 100.0))
                except:
                    pass
        
        # 火災保険のパターン
        fire_insurance_patterns = [
            r'火災保険[：:]\s*([0-9,]+)',
            r'火災[保険]*[：:]\s*([0-9,]+)',
            r'火災保険\s*([0-9,]+)'
        ]
        for pattern in fire_insurance_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['fire_insurance'] = int(match.group(1).replace(',', ''))
                    break
                except:
                    pass
        
        return result

    def extract_rent_from_ocr(self, extracted_text: str) -> Dict:
        """
        OCRテキストから家賃と管理費を抽出（Gemini + 正規表現フォールバック）
        """
        if not extracted_text:
            return {'rent': 0, 'management_fee': 0}
        
        # まずGeminiで抽出
        if self.law_checker and self.law_checker.gemini_available:
            prompt = f"""以下の不動産広告のテキストから、家賃と管理費を抽出してJSON形式で返してください。
各項目が見つからない場合は、該当する項目を0として返してください。

抽出テキスト:
{extracted_text}

抽出項目:
- 家賃: 月額家賃の金額（数値のみ、単位なし。見つからない場合は0）
- 管理費: 月額管理費の金額（数値のみ、単位なし。見つからない場合は0）

JSON形式で、以下の構造で返してください:
{{
  "家賃": 0,
  "管理費": 0
}}

数値のみを返してください。JSONのみを返してください。"""
            try:
                response_text = self.law_checker._call_gemini(prompt)
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    cost_data = json.loads(json_match.group())
                    rent_val = int(cost_data.get('家賃', 0) or 0)
                    mgmt_val = int(cost_data.get('管理費', 0) or 0)
                    if rent_val or mgmt_val:
                        return {'rent': rent_val, 'management_fee': mgmt_val}
            except Exception as e:
                log_error(f"OCRテキストからの家賃抽出エラー: {str(e)}")
        
        # フォールバック: 正規表現で抽出
        rent_val = 0
        mgmt_val = 0
        try:
            rent_match = re.search(r'(賃料|家賃)[：:\s]*([0-9,]+)', extracted_text)
            if rent_match:
                rent_val = int(rent_match.group(2).replace(',', ''))
            mgmt_match = re.search(r'(管理費|共益費)[：:\s]*([0-9,]+)', extracted_text)
            if mgmt_match:
                mgmt_val = int(mgmt_match.group(2).replace(',', ''))
        except Exception:
            pass
        
        return {'rent': rent_val, 'management_fee': mgmt_val}
    
    def estimate_fire_equipment_cost(self, fire_law_result: Optional[Dict] = None) -> Dict:
        """
        消防設備費用を推定（Gemini使用）
        
        Args:
            fire_law_result: 法令判定の消防法結果
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 0, 'breakdown': ''}
        
        # 消防法の結果から必要な情報を抽出
        fire_info = ""
        if fire_law_result:
            fire_info = f"""
消防法判定結果:
{json.dumps(fire_law_result, ensure_ascii=False, indent=2)}
"""
        
        prompt = f"""民泊開業に必要な消防設備費用を推定してください。

{fire_info}

以下の情報を考慮して、消防設備費用を推定してください：
- 消防法上の要件
- 必要な設備の種類と数
- 一般的な設備費用の相場
- **重要**: 自動火災報知設備ではなく特定小規模施設用自動火災報知設備で足りる場合は、無線式の連動型警報機能付感知器を使用することで費用を抑えられる可能性があります。要件を満たす範囲で最も費用効率の良い選択肢を選んでください。

設備の選択指針：
1. 特定小規模施設用自動火災報知設備（無線式連動型警報機能付感知器）が要件を満たす場合は、これを優先的に検討してください（費用を抑えられる）
2. 自動火災報知設備が必要な場合は、標準的な設備を選択してください
3. 消火器、誘導灯、その他の必要な設備も含めてください

以下のJSON形式で返してください：
{{
  "cost": 500000,
  "breakdown": "特定小規模施設用自動火災報知設備（無線式連動型）: ¥200,000、消火器: 2本×¥10,000=¥20,000、誘導灯: 2台×¥15,000=¥30,000、その他: ¥10,000"
}}

費用が見積もれない場合は {{"cost": 0, "breakdown": ""}} を返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 0) or 0)
                    breakdown = result.get('breakdown', '')
                    return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # JSONが見つからない場合は数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"消防設備費用推定エラー: {str(e)}")
        
        return {'cost': 0, 'breakdown': ''}
    
    def estimate_furniture_cost(
        self,
        area: Optional[float] = None,
        occupancy: int = 2,
        layout: Optional[str] = None
    ) -> Dict:
        """
        家具・家電購入費用を推定（Gemini使用）
        
        Args:
            area: 延べ床面積（m²）
            occupancy: 宿泊人数
            layout: 間取り（OCRから抽出）
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 0, 'breakdown': ''}
        
        # プロンプトを作成
        area_info = f"延べ床面積: {area}m²" if area else "延べ床面積: 不明"
        occupancy_info = f"宿泊人数: {occupancy}人"
        layout_info = f"間取り: {layout}" if layout else "間取り: 不明"
        
        prompt = f"""民泊開業に必要な家具・家電購入費用を推定してください。

物件情報:
{area_info}
{occupancy_info}
{layout_info}

購入条件:
- コンセプト: 中価格帯
- ターゲット層: 訪日外国人観光客
- 想定購入先: IKEA、ニトリ、楽天市場、ビンテージショップ、リサイクルショップ

必要な家具・家電:
- ベッド
- テーブル・椅子
- 冷蔵庫
- 洗濯機
- エアコン
- テレビ
- その他必要な家具・家電

以下のJSON形式で返してください：
{{
  "cost": 2000000,
  "breakdown": "ベッド: ¥300,000、テーブル・椅子: ¥150,000、冷蔵庫: ¥80,000、洗濯機: ¥100,000、エアコン: ¥200,000、テレビ: ¥50,000、その他: ¥1,120,000"
}}

費用が見積もれない場合は {{"cost": 0, "breakdown": ""}} を返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 0) or 0)
                    breakdown = result.get('breakdown', '')
                    return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # JSONが見つからない場合は数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"家具・家電購入費用推定エラー: {str(e)}")
        
        return {'cost': 0, 'breakdown': ''}


    def extract_rent_from_ocr(self, extracted_text: str) -> Dict:
        """
        OCRテキストから家賃と管理費を抽出
        
        Args:
            extracted_text: OCRで抽出されたテキスト
            
        Returns:
            家賃と管理費の辞書（rent: 家賃、management_fee: 管理費）
        """
        if not extracted_text or not self.law_checker or not self.law_checker.gemini_available:
            return {'rent': 0, 'management_fee': 0}
        
        prompt = f"""以下の不動産広告のテキストから、家賃と管理費を抽出してJSON形式で返してください。
各項目が見つからない場合は、該当する項目を0として返してください。

抽出テキスト:
{extracted_text}

抽出項目:
- 家賃: 月額家賃の金額（数値のみ、単位なし。見つからない場合は0）
- 管理費: 月額管理費の金額（数値のみ、単位なし。見つからない場合は0）

JSON形式で、以下の構造で返してください:
{{
  "家賃": 0,
  "管理費": 0
}}

数値のみを返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                cost_data = json.loads(json_match.group())
                return {
                    'rent': int(cost_data.get('家賃', 0) or 0),
                    'management_fee': int(cost_data.get('管理費', 0) or 0)
                }
        except Exception as e:
            log_error(f"OCRテキストからの家賃抽出エラー: {str(e)}")
        
        return {'rent': 0, 'management_fee': 0}
    
    def estimate_utilities_cost(
        self,
        area: Optional[float] = None,
        occupancy: int = 2,
        layout: Optional[str] = None
    ) -> Dict:
        """
        水道光熱費を推定（Gemini使用）
        
        Args:
            area: 延べ床面積（m²）
            occupancy: 宿泊人数
            layout: 間取り
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 0, 'breakdown': ''}
        
        area_info = f"延べ床面積: {area}m²" if area else "延べ床面積: 不明"
        occupancy_info = f"宿泊人数: {occupancy}人"
        layout_info = f"間取り: {layout}" if layout else "間取り: 不明"
        
        prompt = f"""民泊開業に必要な月額水道光熱費を推定してください。

物件情報:
{area_info}
{occupancy_info}
{layout_info}

以下の項目を考慮してください：
- 電気代（エアコン、照明、家電など）
- ガス代（給湯、調理など）
- 水道代（洗濯、清掃、宿泊客の使用など）

以下のJSON形式で返してください：
{{
  "cost": 50000,
  "breakdown": "電気代: ¥30,000、ガス代: ¥10,000、水道代: ¥10,000"
}}

費用が見積もれない場合は {{"cost": 0, "breakdown": ""}} を返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 0) or 0)
                    breakdown = result.get('breakdown', '')
                    return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # 数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"水道光熱費推定エラー: {str(e)}")
        
        return {'cost': 0, 'breakdown': ''}
    
    def estimate_insurance_cost(
        self,
        area: Optional[float] = None,
        occupancy: int = 2,
        layout: Optional[str] = None,
        address: Optional[str] = None,
        structure: Optional[str] = None
    ) -> Dict:
        """
        保険費を推定（Gemini使用）
        
        Args:
            area: 延べ床面積（m²）
            occupancy: 宿泊人数
            layout: 間取り
            address: 住所
            structure: 建物構造
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 5000, 'breakdown': 'デフォルト値'}  # デフォルト¥5,000/月
        
        area_info = f"延べ床面積: {area}m²" if area else "延べ床面積: 不明"
        occupancy_info = f"宿泊人数: {occupancy}人"
        layout_info = f"間取り: {layout}" if layout else "間取り: 不明"
        address_info = f"住所: {address}" if address else "住所: 不明"
        structure_info = f"建物構造: {structure}" if structure else "建物構造: 不明"
        
        prompt = f"""民泊開業に必要な月額保険費を推定してください。

物件情報:
{area_info}
{occupancy_info}
{layout_info}
{address_info}
{structure_info}

以下の項目を考慮してください：
- 火災保険
- 個人賠償責任保険
- その他必要な保険

一般的な相場は月額¥3,000〜¥10,000程度です。物件規模や構造に応じて適切な金額を推定してください。

以下のJSON形式で返してください：
{{
  "cost": 5000,
  "breakdown": "火災保険: ¥3,000、個人賠償責任保険: ¥2,000"
}}

費用が見積もれない場合は {{"cost": 5000, "breakdown": "デフォルト値"}} を返してください（デフォルト¥5,000/月）。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 5000) or 5000)
                    breakdown = result.get('breakdown', '')
                    if cost > 0:
                        return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # 数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"保険費推定エラー: {str(e)}")
        
        return {'cost': 5000, 'breakdown': 'デフォルト値'}  # デフォルト¥5,000/月
    
    def estimate_cleaning_cost(
        self,
        area: Optional[float] = None,
        occupancy: int = 2,
        layout: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict:
        """
        清掃費を推定（Gemini使用）
        
        Args:
            area: 延べ床面積（m²）
            occupancy: 宿泊人数
            layout: 間取り
            address: 住所
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 0, 'breakdown': ''}
        
        area_info = f"延べ床面積: {area}m²" if area else "延べ床面積: 不明"
        occupancy_info = f"宿泊人数: {occupancy}人"
        layout_info = f"間取り: {layout}" if layout else "間取り: 不明"
        address_info = f"住所: {address}" if address else "住所: 不明"
        
        prompt = f"""民泊開業に必要な月額清掃費を推定してください。

物件情報:
{area_info}
{occupancy_info}
{layout_info}
{address_info}

以下の項目を考慮してください：
- チェックアウト後の清掃費用（1回あたりの単価×回数）
- 月間の平均宿泊回数から清掃回数を推定
- 地域の清掃業者の相場

以下のJSON形式で返してください：
{{
  "cost": 30000,
  "breakdown": "清掃1回あたり: ¥5,000、月間清掃回数: 6回"
}}

費用が見積もれない場合は {{"cost": 0, "breakdown": ""}} を返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 0) or 0)
                    breakdown = result.get('breakdown', '')
                    return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # 数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"清掃費推定エラー: {str(e)}")
        
        return {'cost': 0, 'breakdown': ''}
    
    def estimate_supplies_cost(
        self,
        area: Optional[float] = None,
        occupancy: int = 2,
        layout: Optional[str] = None
    ) -> Dict:
        """
        消耗品費用を推定（Gemini使用）
        
        Args:
            area: 延べ床面積（m²）
            occupancy: 宿泊人数
            layout: 間取り
            
        Returns:
            推定結果の辞書（cost: 費用、breakdown: 内訳テキスト）
        """
        if not self.law_checker or not self.law_checker.gemini_available:
            return {'cost': 0, 'breakdown': ''}
        
        area_info = f"延べ床面積: {area}m²" if area else "延べ床面積: 不明"
        occupancy_info = f"宿泊人数: {occupancy}人"
        layout_info = f"間取り: {layout}" if layout else "間取り: 不明"
        
        prompt = f"""民泊開業に必要な月額消耗品費用を推定してください。

物件情報:
{area_info}
{occupancy_info}
{layout_info}

以下の項目を考慮してください：
- トイレットペーパー、ティッシュペーパー
- 洗剤、柔軟剤
- タオル、バスタオル（消耗品としての交換）
- アメニティ（歯ブラシ、シャンプーなど）
- その他消耗品

以下のJSON形式で返してください：
{{
  "cost": 10000,
  "breakdown": "アメニティ: ¥5,000、洗剤類: ¥3,000、タオル交換: ¥2,000"
}}

費用が見積もれない場合は {{"cost": 0, "breakdown": ""}} を返してください。JSONのみを返してください。"""
        
        try:
            response_text = self.law_checker._call_gemini(prompt)
            
            # JSONを抽出
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    cost = int(result.get('cost', 0) or 0)
                    breakdown = result.get('breakdown', '')
                    return {'cost': cost, 'breakdown': breakdown}
                except:
                    pass
            
            # 数値のみ抽出（後方互換性）
            numbers = re.findall(r'[0-9,]+', response_text)
            if numbers:
                try:
                    cost = int(numbers[0].replace(',', ''))
                    if cost > 0:
                        return {'cost': cost, 'breakdown': ''}
                except:
                    pass
        except Exception as e:
            log_error(f"消耗品費用推定エラー: {str(e)}")
        
        return {'cost': 0, 'breakdown': ''}


def create_initial_cost_estimator(gemini_api_key: str = "") -> InitialCostEstimator:
    """
    初期費用推定器を作成
    
    Args:
        gemini_api_key: Gemini APIキー
    
    Returns:
        InitialCostEstimatorインスタンス
    """
    return InitialCostEstimator(gemini_api_key=gemini_api_key)

