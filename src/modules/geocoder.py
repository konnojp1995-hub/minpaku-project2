"""
ジオコーディングモジュール
住所から緯度経度を取得する機能を提供
"""
import requests
import json
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .utils import log_error, log_info, validate_coordinates


class Geocoder:
    """住所から緯度経度を取得するクラス"""
    
    def __init__(self, google_api_key: str = "", geocoding_api_key: str = ""):
        """
        初期化
        
        Args:
            google_api_key: Google Maps API キー
            geocoding_api_key: Geocoding.jp API キー
        """
        self.google_api_key = google_api_key
        self.geocoding_api_key = geocoding_api_key
        
        # Google Maps Geocoding API のエンドポイント
        self.google_endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
        
        # Geocoding.jp API のエンドポイント
        self.geocoding_endpoint = "https://www.geocoding.jp/api/"
    
    def geocode_with_google(self, address: str) -> Dict:
        """
        Google Maps APIを使用してジオコーディング
        
        Args:
            address: 住所文字列
            
        Returns:
            ジオコーディング結果の辞書
        """
        if not self.google_api_key:
            return {
                'success': False,
                'error': 'Google Maps API キーが設定されていません'
            }
        
        try:
            params = {
                'address': address,
                'key': self.google_api_key,
                'language': 'ja'
            }
            
            response = requests.get(self.google_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'success': True,
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'method': 'google'
                }
            else:
                return {
                    'success': False,
                    'error': f"Google Maps API エラー: {data.get('status', 'Unknown error')}"
                }
                
        except requests.exceptions.RequestException as e:
            log_error(f"Google Maps API リクエストエラー: {str(e)}")
            return {
                'success': False,
                'error': f"リクエストエラー: {str(e)}"
            }
        except Exception as e:
            log_error(f"Google Maps API 処理エラー: {str(e)}")
            return {
                'success': False,
                'error': f"処理エラー: {str(e)}"
            }
    
    def geocode_with_geocoding_jp(self, address: str) -> Dict:
        """
        Geocoding.jp APIを使用してジオコーディング
        
        Args:
            address: 住所文字列
            
        Returns:
            ジオコーディング結果の辞書
        """
        try:
            params = {
                'q': address
            }
            
            if self.geocoding_api_key:
                params['key'] = self.geocoding_api_key
            
            response = requests.get(self.geocoding_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            # Geocoding.jpはXML形式でレスポンスを返す
            from xml.etree import ElementTree as ET
            
            root = ET.fromstring(response.text)
            
            # エラーチェック
            error_elem = root.find('error')
            if error_elem is not None:
                return {
                    'success': False,
                    'error': f"Geocoding.jp API エラー: {error_elem.text}"
                }
            
            # 座標を取得
            lat_elem = root.find('coordinate/lat')
            lng_elem = root.find('coordinate/lng')
            
            if lat_elem is not None and lng_elem is not None:
                latitude = float(lat_elem.text)
                longitude = float(lng_elem.text)
                
                return {
                    'success': True,
                    'latitude': latitude,
                    'longitude': longitude,
                    'formatted_address': address,
                    'method': 'geocoding_jp'
                }
            else:
                return {
                    'success': False,
                    'error': '座標情報が見つかりませんでした'
                }
                
        except requests.exceptions.RequestException as e:
            log_error(f"Geocoding.jp API リクエストエラー: {str(e)}")
            return {
                'success': False,
                'error': f"リクエストエラー: {str(e)}"
            }
        except Exception as e:
            log_error(f"Geocoding.jp API 処理エラー: {str(e)}")
            return {
                'success': False,
                'error': f"処理エラー: {str(e)}"
            }
    
    def geocode_address(self, address: str) -> Dict:
        """
        住所をジオコーディングする（複数のAPIを試行）
        
        Args:
            address: 住所文字列
            
        Returns:
            ジオコーディング結果の辞書
        """
        log_info(f"住所のジオコーディングを開始: {address}")
        
        # Google Maps API を試行
        if self.google_api_key:
            result = self.geocode_with_google(address)
            if result['success']:
                log_info("Google Maps API でジオコーディング成功")
                return result
        
        # Geocoding.jp API を試行
        result = self.geocode_with_geocoding_jp(address)
        if result['success']:
            log_info("Geocoding.jp API でジオコーディング成功")
            return result
        
        # 両方失敗した場合
        log_error("すべてのジオコーディング API で失敗しました")
        return {
            'success': False,
            'error': 'ジオコーディングに失敗しました',
            'address': address
        }
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """
        緯度経度から住所を取得（逆ジオコーディング）
        
        Args:
            latitude: 緯度
            longitude: 経度
            
        Returns:
            逆ジオコーディング結果の辞書
        """
        if not validate_coordinates(latitude, longitude):
            return {
                'success': False,
                'error': '無効な座標です'
            }
        
        if not self.google_api_key:
            return {
                'success': False,
                'error': 'Google Maps API キーが設定されていません'
            }
        
        try:
            params = {
                'latlng': f"{latitude},{longitude}",
                'key': self.google_api_key,
                'language': 'ja'
            }
            
            response = requests.get(self.google_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                return {
                    'success': True,
                    'formatted_address': result['formatted_address'],
                    'address_components': result.get('address_components', []),
                    'method': 'google_reverse'
                }
            else:
                return {
                    'success': False,
                    'error': f"逆ジオコーディングエラー: {data.get('status', 'Unknown error')}"
                }
                
        except Exception as e:
            log_error(f"逆ジオコーディング処理エラー: {str(e)}")
            return {
                'success': False,
                'error': f"処理エラー: {str(e)}"
            }
    
    def batch_geocode(self, addresses: List[str]) -> List[Dict]:
        """
        複数の住所を一括でジオコーディング
        
        Args:
            addresses: 住所のリスト
            
        Returns:
            ジオコーディング結果のリスト
        """
        results = []
        
        for i, address in enumerate(addresses):
            log_info(f"ジオコーディング進行状況: {i+1}/{len(addresses)}")
            
            result = self.geocode_address(address)
            result['original_address'] = address
            results.append(result)
            
            # API制限を考慮して少し待機
            if i < len(addresses) - 1:
                import time
                time.sleep(0.1)
        
        return results
    
    def get_best_result(self, results: List[Dict]) -> Optional[Dict]:
        """
        複数のジオコーディング結果から最適なものを選択
        
        Args:
            results: ジオコーディング結果のリスト
            
        Returns:
            最適な結果の辞書
        """
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return None
        
        # Google Maps API の結果を優先
        google_results = [r for r in successful_results if r.get('method') == 'google']
        if google_results:
            return google_results[0]
        
        # Geocoding.jp の結果を返す
        return successful_results[0]


def create_geocoder(google_api_key: str = "", geocoding_api_key: str = "") -> Geocoder:
    """
    ジオコーダーを作成する
    
    Args:
        google_api_key: Google Maps API キー
        geocoding_api_key: Geocoding.jp API キー
        
    Returns:
        Geocoderインスタンス
    """
    return Geocoder(google_api_key, geocoding_api_key)

