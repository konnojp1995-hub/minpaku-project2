"""
法令の根拠となる参考リンクを管理するモジュール
"""
from typing import Dict, Optional, List, Tuple
import urllib.parse
import requests


# 法令ごとの基本情報と該当条文
LAW_ARTICLES: Dict[str, Dict[str, any]] = {
    "民泊新法": {
        "name": "住宅宿泊事業法",
        "articles": {
            "許可判定": ["第3条", "第4条"],
            "主な理由": ["第3条", "第4条"],
            "その他制限": ["第5条", "第6条"]
        }
    },
    "旅館業法": {
        "name": "旅館業法",
        "articles": {
            "許可判定": ["第3条"],
            "主な理由": ["第3条", "第4条"],
            "その他制限": ["第5条", "第6条"]
        }
    },
    "特区民泊": {
        "name": "国家戦略特別区域における特定居住用施設の活用に関する特別措置法",
        "articles": {
            "許可判定": ["第3条"],
            "主な理由": ["第3条", "第4条"],
            "その他制限": ["第5条"]
        }
    },
    "消防法": {
        "name": "消防法",
        "articles": {
            "火災報知器": ["第9条の2", "第17条の3"],
            "竪穴区画": ["第8条", "第17条の2"],
            "その他留意点": ["第8条", "第9条", "第17条"]
        }
    },
    "建築基準法": {
        "name": "建築基準法",
        "articles": {
            "用途変更": ["第6条", "第27条"],
            "竪穴区画": ["第27条", "第35条"],
            "その他制限": ["第35条", "第52条"],
            "接道義務": ["第43条"]
        }
    }
}


def generate_egov_search_url(law_name: str, article: str = "") -> str:
    """
    e-Gov法令検索の検索結果URLを生成する
    
    Args:
        law_name: 法令名（例: "旅館業法", "住宅宿泊事業法"）
        article: 条文（例: "第3条"、空の場合は法令名のみ）
    
    Returns:
        e-Gov法令検索のURL
    """
    base_url = "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0100/result"
    
    if article:
        search_query = f"{law_name} {article}"
    else:
        search_query = law_name
    
    params = {"searchLawName": search_query}
    url = f"{base_url}?{urllib.parse.urlencode(params, encoding='utf-8')}"
    return url


def check_url_exists(url: str, timeout: int = 5) -> bool:
    """
    URLが存在するか確認する
    
    Args:
        url: 確認するURL
        timeout: タイムアウト秒数
    
    Returns:
        URLが存在する場合はTrue、それ以外はFalse
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        # HEADが失敗した場合はGETを試す
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            return response.status_code < 400
        except Exception:
            return False


def get_law_article_link(law_name: str, category: str = "") -> Optional[str]:
    """
    法令名とカテゴリから該当条文のリンクを取得（e-Gov法令検索）
    
    Args:
        law_name: 法令名（例: "民泊新法", "旅館業法"）
        category: カテゴリ（例: "許可判定", "主な理由", "火災報知器"）
    
    Returns:
        Markdown形式のリンク文字列（存在しない場合はNone）
    """
    if law_name not in LAW_ARTICLES:
        return None
    
    law_info = LAW_ARTICLES[law_name]
    law_full_name = law_info["name"]
    
    # カテゴリに対応する条文を取得
    articles = law_info.get("articles", {}).get(category, [])
    if not articles:
        # カテゴリが無い場合は法令名のみで検索
        url = generate_egov_search_url(law_full_name)
        # e-GovのURLは常に存在すると仮定（検索ページなので）
        return f"[🔗]({url})"
    
    # 最初の条文を使用
    article = articles[0]
    url = generate_egov_search_url(law_full_name, article)
    
    # e-Govの検索URLは常に存在すると仮定
    return f"[🔗]({url})"


def get_law_article_text(law_name: str, category: str = "") -> Optional[str]:
    """
    法令名とカテゴリから該当条文のテキストを取得
    
    Args:
        law_name: 法令名（例: "民泊新法", "旅館業法"）
        category: カテゴリ（例: "許可判定", "主な理由", "火災報知器"）
    
    Returns:
        法令名と条文のテキスト（例: "住宅宿泊事業法 第3条"、存在しない場合はNone）
    """
    if law_name not in LAW_ARTICLES:
        return None
    
    law_info = LAW_ARTICLES[law_name]
    law_full_name = law_info["name"]
    
    # カテゴリに対応する条文を取得
    articles = law_info.get("articles", {}).get(category, [])
    if not articles:
        return None
    
    # 最初の条文を使用
    article = articles[0]
    return f"{law_full_name} {article}"


def get_law_reference_link(law_name: str) -> Optional[str]:
    """
    法令名から参考リンクのMarkdown形式を取得（非推奨、get_law_article_linkを使用すること）
    
    Args:
        law_name: 法令名（例: "民泊新法", "旅館業法"）
    
    Returns:
        Markdown形式のリンク文字列（存在しない場合はNone）
    """
    # この関数は後方互換性のために残すが、新しいコードではget_law_article_linkを使用すること
    if law_name not in LAW_ARTICLES:
        return None
    
    law_info = LAW_ARTICLES[law_name]
    law_full_name = law_info["name"]
    url = generate_egov_search_url(law_full_name)
    return f"[🔗]({url})"
