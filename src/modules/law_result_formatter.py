"""
法令判定結果のフォーマッター
統一された形式で法令判定結果を整形する
"""
from typing import Dict, List, Optional


def format_law_check_results(property_info: Dict, minpaku_result: Dict, 
                             ryokan_result: Dict, tokku_result: Dict,
                             fire_result: Dict, building_result: Dict,
                             local_result: Dict) -> str:
    """
    法令判定結果を指定フォーマットで整形する
    
    Args:
        property_info: 物件情報
        minpaku_result: 民泊新法の判定結果
        ryokan_result: 旅館業法の判定結果
        tokku_result: 特区民泊の判定結果
        fire_result: 消防法上の要件
        building_result: 建築基準法上の要件
        local_result: 自治体の制限
        
    Returns:
        整形された結果テキスト
    """
    lines = []
    
    # 1. 物件情報
    lines.append("**1. 物件情報**")
    lines.append("")
    
    lines.append(f"所在地: {property_info.get('所在地', '不明')}")
    lines.append("")
    lines.append(f"建物用途: {property_info.get('建物用途', '不明')}")
    lines.append("")
    lines.append(f"構造: {property_info.get('構造', '不明')}")
    lines.append("")
    lines.append(f"階数: {property_info.get('階数', '不明')}")
    lines.append("")
    lines.append(f"用途地域: {property_info.get('用途地域', '不明')}")
    lines.append("")
    floor_area = property_info.get('延べ床面積', '不明')
    if floor_area != '不明':
        lines.append(f"延べ床面積: {floor_area}㎡")
    else:
        lines.append(f"延べ床面積: {floor_area}")
    lines.append("")
    lines.append("")
    
    # 2. 民泊の許可判定
    lines.append("**2. 民泊の許可判定**")
    lines.append("")
    
    # 2.1 民泊新法
    lines.append("**2.1 民泊新法**")
    lines.append("")
    if minpaku_result.get('success'):
        permission_text = minpaku_result.get('permission', '')
        # 許可判定、主な理由、その他制限を抽出
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    lines.append("")
    
    # 2.2 旅館業
    lines.append("**2.2 旅館業**")
    lines.append("")
    if ryokan_result.get('success'):
        permission_text = ryokan_result.get('permission', '')
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    lines.append("")
    
    # 2.3 特区民泊
    lines.append("**2.3 特区民泊**")
    lines.append("")
    if tokku_result.get('success'):
        permission_text = tokku_result.get('permission', '')
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    lines.append("")
    
    # 3. 消防法上のポイント
    lines.append("**3. 消防法上のポイント**")
    lines.append("")
    if fire_result.get('success'):
        requirements_text = fire_result.get('requirements', '')
        formatted = _parse_requirements_internal(requirements_text, ['火災報知器', '竪穴区画', 'その他留意点'])
        lines.append(f"火災報知器: {formatted.get('火災報知器', '不明')}")
        lines.append("")
        lines.append(f"竪穴区画: {formatted.get('竪穴区画', '不明')}")
        lines.append("")
        lines.append(f"その他留意点: {formatted.get('その他留意点', '特になし')}")
    else:
        lines.append("火災報知器: 判定不可")
        lines.append("")
        lines.append("竪穴区画: 判定不可")
        lines.append("")
        lines.append("その他留意点: 判定不可")
    lines.append("")
    lines.append("")
    
    # 4. 建築基準法上のポイント
    lines.append("**4. 建築基準法上のポイント**")
    lines.append("")
    if building_result.get('success'):
        requirements_text = building_result.get('requirements', '')
        formatted = _parse_requirements_internal(requirements_text, ['用途変更', '竪穴区画', 'その他制限', '接道義務'])
        lines.append(f"用途変更: {formatted.get('用途変更', '不明')}")
        lines.append("")
        lines.append(f"竪穴区画: {formatted.get('竪穴区画', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('その他制限', '特になし')}")
        lines.append("")
        lines.append(f"接道義務: {formatted.get('接道義務', '不明')}")
    else:
        lines.append("用途変更: 判定不可")
        lines.append("")
        lines.append("竪穴区画: 判定不可")
        lines.append("")
        lines.append("その他制限: 判定不可")
        lines.append("")
        lines.append("接道義務: 判定不可")
    lines.append("")
    lines.append("")
    
    # 5. その他の留意点
    lines.append("**5. その他の留意点**")
    lines.append("")
    if local_result.get('success'):
        restrictions = local_result.get('restrictions', '特になし')
        # 1行にまとめる
        restrictions = restrictions.strip().replace('\n', ' ').strip()
        if not restrictions or restrictions == '':
            restrictions = '特になし'
        lines.append(restrictions)
    else:
        lines.append("特になし")
    
    return "\n".join(lines)


def parse_permission_result(text: str) -> Dict[str, str]:
    """
    許可判定結果テキストをパースする（公開API）
    
    Args:
        text: 判定結果テキスト
        
    Returns:
        パースされた結果の辞書
    """
    return _parse_permission_result_internal(text)


def _parse_permission_result_internal(text: str) -> Dict[str, str]:
    """
    許可判定結果テキストをパースする
    
    Args:
        text: 判定結果テキスト
        
    Returns:
        パースされた結果の辞書
    """
    result = {
        '判定': '不明',
        '理由': '不明',
        '制限': '特になし'
    }
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('許可判定:'):
            result['判定'] = line.replace('許可判定:', '').strip()
        elif line.startswith('主な理由:'):
            result['理由'] = line.replace('主な理由:', '').strip()
        elif line.startswith('その他制限:'):
            result['制限'] = line.replace('その他制限:', '').strip()
    
    return result


def parse_requirements(text: str, keys: List[str]) -> Dict[str, str]:
    """
    要件テキストをパースする（公開API）
    
    Args:
        text: 要件テキスト
        keys: 抽出するキーのリスト
        
    Returns:
        パースされた結果の辞書
    """
    return _parse_requirements_internal(text, keys)


def _parse_requirements_internal(text: str, keys: List[str]) -> Dict[str, str]:
    """
    要件テキストをパースする
    
    Args:
        text: 要件テキスト
        keys: 抽出するキーのリスト
        
    Returns:
        パースされた結果の辞書
    """
    result = {key: '不明' for key in keys}
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        for key in keys:
            if line.startswith(f'{key}:'):
                result[key] = line.replace(f'{key}:', '').strip()
                break
    
    return result


def format_property_info(property_info: Dict) -> str:
    """物件情報をフォーマットする"""
    lines = []
    lines.append("**1. 物件情報**")
    lines.append("")
    lines.append(f"所在地: {property_info.get('所在地', '不明')}")
    lines.append("")
    lines.append(f"建物用途: {property_info.get('建物用途', '不明')}")
    lines.append("")
    lines.append(f"構造: {property_info.get('構造', '不明')}")
    lines.append("")
    lines.append(f"階数: {property_info.get('階数', '不明')}")
    lines.append("")
    lines.append(f"用途地域: {property_info.get('用途地域', '不明')}")
    lines.append("")
    floor_area = property_info.get('延べ床面積', '不明')
    if floor_area != '不明':
        lines.append(f"延べ床面積: {floor_area}㎡")
    else:
        lines.append(f"延べ床面積: {floor_area}")
    lines.append("")
    return "\n".join(lines)


def format_permission_results(minpaku_result: Dict, ryokan_result: Dict, tokku_result: Dict) -> str:
    """民泊の許可判定結果をフォーマットする"""
    lines = []
    lines.append("**2. 民泊の許可判定**")
    lines.append("")
    
    # 2.1 民泊新法
    lines.append("**2.1 民泊新法**")
    lines.append("")
    if minpaku_result.get('success'):
        permission_text = minpaku_result.get('permission', '')
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    lines.append("")
    
    # 2.2 旅館業
    lines.append("**2.2 旅館業**")
    lines.append("")
    if ryokan_result.get('success'):
        permission_text = ryokan_result.get('permission', '')
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    lines.append("")
    
    # 2.3 特区民泊
    lines.append("**2.3 特区民泊**")
    lines.append("")
    if tokku_result.get('success'):
        permission_text = tokku_result.get('permission', '')
        formatted = _parse_permission_result_internal(permission_text)
        lines.append(f"許可判定: {formatted.get('判定', '判定不可')}")
        lines.append("")
        lines.append(f"主な理由: {formatted.get('理由', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('制限', '特になし')}")
    else:
        lines.append("許可判定: 判定不可")
        lines.append("")
        lines.append("主な理由: 判定エラー")
        lines.append("")
        lines.append("その他制限: 特になし")
    lines.append("")
    
    return "\n".join(lines)


def format_fire_law_results(fire_result: Dict) -> str:
    """消防法上のポイントをフォーマットする"""
    lines = []
    lines.append("**3. 消防法上のポイント**")
    lines.append("")
    if fire_result.get('success'):
        requirements_text = fire_result.get('requirements', '')
        formatted = _parse_requirements_internal(requirements_text, ['火災報知器', '竪穴区画', 'その他留意点'])
        lines.append(f"火災報知器: {formatted.get('火災報知器', '不明')}")
        lines.append("")
        lines.append(f"竪穴区画: {formatted.get('竪穴区画', '不明')}")
        lines.append("")
        lines.append(f"その他留意点: {formatted.get('その他留意点', '特になし')}")
    else:
        lines.append("火災報知器: 判定不可")
        lines.append("")
        lines.append("竪穴区画: 判定不可")
        lines.append("")
        lines.append("その他留意点: 判定不可")
    lines.append("")
    
    return "\n".join(lines)


def format_building_standards_results(building_result: Dict) -> str:
    """建築基準法上のポイントをフォーマットする"""
    lines = []
    lines.append("**4. 建築基準法上のポイント**")
    lines.append("")
    if building_result.get('success'):
        requirements_text = building_result.get('requirements', '')
        formatted = _parse_requirements_internal(requirements_text, ['用途変更', '竪穴区画', 'その他制限', '接道義務'])
        lines.append(f"用途変更: {formatted.get('用途変更', '不明')}")
        lines.append("")
        lines.append(f"竪穴区画: {formatted.get('竪穴区画', '不明')}")
        lines.append("")
        lines.append(f"その他制限: {formatted.get('その他制限', '特になし')}")
        lines.append("")
        lines.append(f"接道義務: {formatted.get('接道義務', '不明')}")
    else:
        lines.append("用途変更: 判定不可")
        lines.append("")
        lines.append("竪穴区画: 判定不可")
        lines.append("")
        lines.append("その他制限: 判定不可")
        lines.append("")
        lines.append("接道義務: 判定不可")
    lines.append("")
    
    return "\n".join(lines)


def format_local_restrictions(local_result: Dict) -> str:
    """その他の留意点をフォーマットする"""
    lines = []
    lines.append("**5. その他の留意点**")
    lines.append("")
    if local_result.get('success'):
        restrictions = local_result.get('restrictions', '特になし')
        restrictions = restrictions.strip().replace('\n', ' ').strip()
        if not restrictions or restrictions == '':
            restrictions = '特になし'
        lines.append(restrictions)
    else:
        lines.append("特になし")
    
    return "\n".join(lines)

