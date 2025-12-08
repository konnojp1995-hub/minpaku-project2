"""
ユーティリティ関数モジュール
共通のユーティリティ関数を提供
"""
import os
import json
import re
import sys
from typing import Dict, List, Optional
import streamlit as st


def log_info(message: str) -> None:
    """情報ログを出力する（UIとターミナル両方に出力）"""
    info_text = f"{message}"
    st.info(info_text)
    print(f"[INFO] {info_text}")


def log_error(error_message: str, exception: Optional[Exception] = None) -> None:
    """エラーログを出力する（UIとターミナル両方に出力）"""
    error_text = f"エラー: {error_message}"
    st.error(error_text)
    print(f"[ERROR] {error_text}", file=sys.stderr)
    if exception:
        exception_text = f"詳細: {str(exception)}"
        st.error(exception_text)
        print(f"[ERROR] {exception_text}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


def log_warning(message: str) -> None:
    """警告ログを出力する（UIとターミナル両方に出力）"""
    warning_text = f"⚠️ {message}"
    st.warning(warning_text)
    print(f"[WARNING] {warning_text}")


def log_success(message: str) -> None:
    """成功ログを出力する（UIとターミナル両方に出力）"""
    success_text = f"✅ {message}"
    st.success(success_text)
    print(f"[SUCCESS] {success_text}")


def load_env_config() -> Dict:
    """環境変数から設定を読み込む"""
    config = {}
    
    # python-dotenvを使用して.envファイルを読み込む（利用可能な場合）
    try:
        from dotenv import load_dotenv
        # .envファイルを読み込む（プロジェクトルートから）
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            # プロジェクトルートの.envファイルを探す
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            env_path = os.path.join(project_root, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
            else:
                # カレントディレクトリからも探す
                load_dotenv()
    except ImportError:
        # python-dotenvがインストールされていない場合は手動で読み込む
        pass
    
    # 環境変数から設定を読み込む（.envファイルから読み込んだ値も含む）
    env_vars = [
        'GOOGLE_MAPS_API_KEY',
        'GEMINI_API_KEY',
        'GEOCODING_API_KEY',
        'TESSERACT_CMD',
        'DEBUG',
        'MAX_FILE_SIZE_MB'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # キー名を小文字のスネークケースに変換
            config_key = var.lower()
            
            # 数値型の値は適切に変換
            if var in ['MAX_FILE_SIZE_MB', 'DEBUG']:
                try:
                    if var == 'DEBUG':
                        # ブール値として扱う
                        config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
                    else:
                        # 整数として扱う
                        config[config_key] = int(value)
                except ValueError:
                    # 変換できない場合は文字列のまま
                    config[config_key] = value
            else:
                config[config_key] = value
    
    # 後方互換性のため、env.txtファイルも読み込む（.envファイルが優先）
    env_file = "env.txt"
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # env.txtの値は、環境変数で既に設定されていない場合のみ使用
                            config_key = key.lower()
                            if config_key not in config:
                                # 数値型の値は適切に変換
                                if key.upper() in ['MAX_FILE_SIZE_MB']:
                                    try:
                                        config[config_key] = int(value)
                                    except ValueError:
                                        config[config_key] = value
                                elif key.upper() == 'DEBUG':
                                    try:
                                        config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
                                    except:
                                        config[config_key] = value
                                else:
                                    config[config_key] = value
        except Exception as e:
            print(f"環境変数ファイルの読み込みエラー: {str(e)}")
    
    # 後方互換性のため、キー名のマッピング
    # google_maps_api_key -> google_maps_api_key (そのまま)
    # gemini_api_key -> gemini_api_key (そのまま)
    # geocoding_api_key -> geocoding_api_key (そのまま)
    # max_file_size_mb -> max_file_size_mb (そのまま)
    
    return config


def load_rules() -> Dict:
    """ルールファイルを読み込む"""
    rules_file = "rules.json"
    if os.path.exists(rules_file):
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ルールファイルの読み込みエラー: {str(e)}")
    return {}


def extract_prefecture_from_address(address: str) -> Optional[str]:
    """住所から都道府県を抽出する"""
    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
        "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
        "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
        "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
        "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
        "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
    ]
    
    for prefecture in prefectures:
        if address.startswith(prefecture):
            return prefecture
    return None


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """緯度経度が有効かチェックする"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def validate_file_size(file_path: str, max_size_mb: int = 10) -> bool:
    """ファイルサイズをチェックする"""
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return size_mb <= max_size_mb
    except:
        return False
