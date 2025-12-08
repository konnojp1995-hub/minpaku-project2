"""
用途地域判定モジュール
緯度経度から用途地域を判定する機能を提供
"""
import os
import json
import glob
from typing import Dict, List, Optional, Tuple
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.errors import ShapelyError
import streamlit as st
from .utils import log_error, log_info, extract_prefecture_from_address


class ZoningChecker:
    """用途地域を判定するクラス"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初期化
        
        Args:
            data_dir: GeoJSONファイルが格納されているディレクトリ
        """
        # 相対パスの場合はプロジェクトルートからの絶対パスに変換
        if not os.path.isabs(data_dir):
            # src/modules/zoning_checker.py から見て、プロジェクトルートは ../../ の位置
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_file_dir))
            self.data_dir = os.path.join(project_root, data_dir)
        else:
            self.data_dir = data_dir
        
        self.geojson_files = {}
        self.gdf_cache = {}
        
        # 利用可能なGeoJSONファイルをスキャン
        self._scan_geojson_files()
    
    def _scan_geojson_files(self) -> None:
        """GeoJSONファイルをスキャンしてキャッシュする"""
        try:
            # 都道府県ディレクトリをスキャン
            for prefecture_dir in os.listdir(self.data_dir):
                prefecture_path = os.path.join(self.data_dir, prefecture_dir)
                
                if os.path.isdir(prefecture_path):
                    # GeoJSONファイルを検索
                    geojson_pattern = os.path.join(prefecture_path, "*.geojson")
                    geojson_files = glob.glob(geojson_pattern)
                    
                    if geojson_files:
                        self.geojson_files[prefecture_dir] = geojson_files
                        log_info(f"{prefecture_dir}のGeoJSONファイルを{len(geojson_files)}件発見")
        
        except Exception as e:
            log_error(f"GeoJSONファイルのスキャンでエラー: {str(e)}")
    
    def _load_geojson_file(self, file_path: str) -> Optional[gpd.GeoDataFrame]:
        """
        GeoJSONファイルを読み込む
        
        Args:
            file_path: GeoJSONファイルのパス
            
        Returns:
            GeoDataFrameまたはNone
        """
        try:
            if file_path in self.gdf_cache:
                return self.gdf_cache[file_path]
            
            gdf = gpd.read_file(file_path)
            
            # 座標参照系を設定（WGS84）
            if gdf.crs is None:
                gdf.crs = "EPSG:4326"
            
            # キャッシュに保存
            self.gdf_cache[file_path] = gdf
            
            return gdf
            
        except Exception as e:
            log_error(f"GeoJSONファイルの読み込みエラー ({file_path}): {str(e)}")
            return None
    
    def _find_matching_geojson_files(self, prefecture: str) -> List[str]:
        """
        都道府県に対応するGeoJSONファイルを検索
        
        Args:
            prefecture: 都道府県名（日本語またはローマ字小文字）
            
        Returns:
            対応するGeoJSONファイルのパスのリスト
        """
        # 都道府県名をローマ字に変換（日本語の都道府県名の場合）
        prefecture_roman = self._convert_prefecture_to_roman(prefecture)
        
        # まずローマ字で検索
        if prefecture_roman in self.geojson_files:
            return self.geojson_files[prefecture_roman]
        
        # 次に元の都道府県名で検索（既にローマ字の場合）
        if prefecture in self.geojson_files:
            return self.geojson_files[prefecture]
        
        return []
    
    def _convert_prefecture_to_roman(self, prefecture: str) -> str:
        """
        都道府県名をローマ字に変換
        
        Args:
            prefecture: 都道府県名（日本語）
            
        Returns:
            ローマ字の都道府県名（小文字）
        """
        # 都道府県名のマッピング
        prefecture_map = {
            '北海道': 'hokkaido',
            '青森県': 'aomori',
            '岩手県': 'iwate',
            '宮城県': 'miyagi',
            '秋田県': 'akita',
            '山形県': 'yamagata',
            '福島県': 'fukushima',
            '茨城県': 'ibaraki',
            '栃木県': 'tochigi',
            '群馬県': 'gunma',
            '埼玉県': 'saitama',
            '千葉県': 'chiba',
            '東京都': 'tokyo',
            '神奈川県': 'kanagawa',
            '新潟県': 'niigata',
            '富山県': 'toyama',
            '石川県': 'ishikawa',
            '福井県': 'fukui',
            '山梨県': 'yamanashi',
            '長野県': 'nagano',
            '岐阜県': 'gifu',
            '静岡県': 'shizuoka',
            '愛知県': 'aichi',
            '三重県': 'mie',
            '滋賀県': 'shiga',
            '京都府': 'kyoto',
            '大阪府': 'osaka',
            '兵庫県': 'hyogo',
            '奈良県': 'nara',
            '和歌山県': 'wakayama',
            '鳥取県': 'tottori',
            '島根県': 'shimane',
            '岡山県': 'okayama',
            '広島県': 'hiroshima',
            '山口県': 'yamaguchi',
            '徳島県': 'tokushima',
            '香川県': 'kagawa',
            '愛媛県': 'ehime',
            '高知県': 'kochi',
            '福岡県': 'fukuoka',
            '佐賀県': 'saga',
            '長崎県': 'nagasaki',
            '熊本県': 'kumamoto',
            '大分県': 'oita',
            '宮崎県': 'miyazaki',
            '鹿児島県': 'kagoshima',
            '沖縄県': 'okinawa'
        }
        
        if not prefecture:
            return prefecture
        
        # マッピングから取得
        roman = prefecture_map.get(prefecture, prefecture.lower())
        
        return roman
    
    def _point_in_polygon(self, point: Point, gdf: gpd.GeoDataFrame) -> Optional[Dict]:
        """
        ポイントがポリゴン内にあるかチェック
        
        Args:
            point: チェックするポイント
            gdf: GeoDataFrame
            
        Returns:
            マッチしたポリゴンの情報またはNone
        """
        try:
            # 座標参照系が異なる場合は変換
            if gdf.crs is None or (hasattr(gdf.crs, 'to_string') and gdf.crs.to_string() != 'EPSG:4326'):
                try:
                    if gdf.crs and hasattr(gdf.crs, 'to_string') and gdf.crs.to_string() != 'EPSG:4326':
                        gdf = gdf.to_crs('EPSG:4326')
                    elif gdf.crs is None:
                        gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                except Exception as crs_error:
                    log_warning(f"座標参照系の変換エラー（無視します）: {str(crs_error)}")
            
            # 空間インデックスを使用して効率的に検索
            try:
                # GeoDataFrameの空間インデックスを作成（存在しない場合）
                if not hasattr(gdf, 'sindex') or gdf.sindex is None:
                    try:
                        gdf.sindex = gdf.sindex if hasattr(gdf, 'sindex') else None
                    except:
                        pass
                
                # 空間インデックスを使用して候補を取得
                spatial_index = gdf.sindex if hasattr(gdf, 'sindex') and gdf.sindex is not None else None
                
                if spatial_index is not None:
                    try:
                        # 境界ボックスを使用して候補を取得
                        candidate_idx = list(spatial_index.intersection(point.bounds))
                        
                        # 候補の中から正確にチェック
                        for idx in candidate_idx:
                            try:
                                row = gdf.iloc[idx]
                                if row.geometry.contains(point):
                                    # propertiesからgeometryを除外
                                    row_dict = row.to_dict()
                                    if 'geometry' in row_dict:
                                        del row_dict['geometry']
                                    return {
                                        'index': idx,
                                        'properties': row_dict
                                    }
                            except Exception:
                                continue
                    except Exception as sindex_error:
                        log_warning(f"空間インデックスの使用に失敗。通常の方法で検索します: {str(sindex_error)}")
                        # 通常の方法にフォールバック
                        spatial_index = None
                
                # 空間インデックスが利用できない場合は全件チェック
                if spatial_index is None:
                    for idx, row in gdf.iterrows():
                        try:
                            if row.geometry.contains(point):
                                # propertiesからgeometryを除外
                                row_dict = row.to_dict()
                                if 'geometry' in row_dict:
                                    del row_dict['geometry']
                                return {
                                    'index': idx,
                                    'properties': row_dict
                                }
                        except Exception as row_error:
                            # 特定の行でエラーが発生しても続行
                            continue
                            
            except Exception as iter_error:
                # 反復処理に失敗した場合のフォールバック
                log_warning(f"反復処理エラー: {str(iter_error)}")
                # 最小限のチェック
                try:
                    for idx in range(min(100, len(gdf))):  # 最初の100件のみチェック（フォールバック）
                        row = gdf.iloc[idx]
                        if row.geometry.contains(point):
                            # propertiesからgeometryを除外
                            row_dict = row.to_dict()
                            if 'geometry' in row_dict:
                                del row_dict['geometry']
                            return {
                                'index': idx,
                                'properties': row_dict
                            }
                except Exception:
                    pass
            
            return None
            
        except ShapelyError as e:
            log_error(f"空間演算エラー: {str(e)}")
            return None
        except Exception as e:
            log_error(f"ポイント・ポリゴン判定エラー: {str(e)}")
            import traceback
            log_error(f"詳細: {traceback.format_exc()}")
            return None
    
    def check_zoning_by_coordinates(self, latitude: float, longitude: float, 
                                  prefecture: str = None) -> Dict:
        """
        緯度経度から用途地域を判定
        
        Args:
            latitude: 緯度
            longitude: 経度
            prefecture: 都道府県名（日本語またはローマ字小文字、省略可）
            
        Returns:
            用途地域判定結果の辞書
        """
        try:
            # ポイントオブジェクトを作成
            point = Point(longitude, latitude)
            
            # 都道府県が指定されている場合
            if prefecture:
                geojson_files = self._find_matching_geojson_files(prefecture)
                if not geojson_files:
                    log_warning(f"都道府県 '{prefecture}' のGeoJSONファイルが見つかりませんでした。すべてのファイルを検索します。")
                    # 都道府県が見つからない場合は、すべてのファイルをチェック
                    geojson_files = []
                    for files in self.geojson_files.values():
                        geojson_files.extend(files)
            else:
                # 都道府県が指定されていない場合は、利用可能なすべてのファイルをチェック
                geojson_files = []
                for files in self.geojson_files.values():
                    geojson_files.extend(files)
            
            if not geojson_files:
                log_error(f"GeoJSONファイルが見つかりませんでした。dataディレクトリを確認してください。")
                return {
                    'success': False,
                    'error': '対応するGeoJSONファイルが見つかりません',
                    'zoning_type': None,
                    'zoning_code': None,
                    'file_checked': []
                }
            
            log_info(f"用途地域判定を開始: ({latitude}, {longitude}), チェック対象ファイル数: {len(geojson_files)}")
            
            # 各GeoJSONファイルをチェック
            checked_files_count = 0
            for file_path in geojson_files:
                gdf = self._load_geojson_file(file_path)
                
                if gdf is None:
                    log_warning(f"GeoJSONファイルの読み込みに失敗: {file_path}")
                    continue
                
                checked_files_count += 1
                
                # ポイントがポリゴン内にあるかチェック
                match_result = self._point_in_polygon(point, gdf)
                
                if match_result:
                    properties = match_result['properties']
                    
                    # 用途地域情報を抽出（複数のキー名に対応）
                    # まず、propertiesが辞書でない場合は変換
                    if not isinstance(properties, dict):
                        if hasattr(properties, 'to_dict'):
                            properties = properties.to_dict()
                        else:
                            properties = {}
                    
                    # 用途地域名を抽出（複数のキー名を試行）
                    zoning_type = None
                    for key in ['A29_005', '用途地域', 'name', 'ZoningType', 'zoning_type', 'ZONING_TYPE', '用途地域名']:
                        if key in properties and properties[key]:
                            zoning_type = str(properties[key]).strip()
                            if zoning_type and zoning_type != 'None' and zoning_type != '':
                                break
                    
                    if not zoning_type:
                        zoning_type = '不明'
                    
                    # 用途地域コードを抽出
                    zoning_code = None
                    for key in ['A29_004', '用途地域コード', 'code', 'ZoningCode', 'zoning_code', 'ZONING_CODE', '用途地域コード']:
                        if key in properties and properties[key]:
                            zoning_code = str(properties[key]).strip()
                            if zoning_code and zoning_code != 'None' and zoning_code != '':
                                break
                    
                    if not zoning_code:
                        zoning_code = ''
                    
                    if zoning_type and zoning_type != '不明':
                        log_info(f"用途地域を特定: {zoning_type} (ファイル: {os.path.basename(file_path)})")
                        
                        return {
                            'success': True,
                            'zoning_type': zoning_type,
                            'zoning_code': zoning_code,
                            'properties': properties,
                            'file_path': file_path,
                            'coordinates': {
                                'latitude': latitude,
                                'longitude': longitude
                            }
                        }
            
            # マッチしなかった場合
            log_warning(f"用途地域が見つかりませんでした。チェックしたファイル数: {checked_files_count}/{len(geojson_files)}")
            return {
                'success': False,
                'error': f'指定された座標({latitude}, {longitude})の用途地域が見つかりませんでした。チェックしたファイル数: {checked_files_count}',
                'zoning_type': None,
                'zoning_code': None,
                'file_checked': geojson_files[:5] if len(geojson_files) > 5 else geojson_files  # 最初の5件のみ表示
            }
            
        except Exception as e:
            log_error(f"用途地域判定でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"判定エラー: {str(e)}",
                'zoning_type': None,
                'zoning_code': None
            }
    
    def check_zoning_by_address(self, address: str) -> Dict:
        """
        住所から用途地域を判定
        
        Args:
            address: 住所文字列
            
        Returns:
            用途地域判定結果の辞書
        """
        try:
            # 住所から都道府県を抽出
            prefecture = extract_prefecture_from_address(address)
            
            if not prefecture:
                return {
                    'success': False,
                    'error': '住所から都道府県を特定できませんでした',
                    'address': address
                }
            
            # 住所をジオコーディング（簡易版）
            # 実際の実装では、geocoderモジュールを使用
            log_info(f"住所から用途地域を判定: {address}")
            
            # 都道府県に対応するGeoJSONファイルをチェック
            geojson_files = self._find_matching_geojson_files(prefecture)
            
            if not geojson_files:
                return {
                    'success': False,
                    'error': f'{prefecture}のGeoJSONファイルが見つかりません',
                    'address': address,
                    'prefecture': prefecture
                }
            
            return {
                'success': True,
                'message': f'{prefecture}のGeoJSONファイルを{len(geojson_files)}件発見',
                'address': address,
                'prefecture': prefecture,
                'available_files': geojson_files
            }
            
        except Exception as e:
            log_error(f"住所からの用途地域判定でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"判定エラー: {str(e)}",
                'address': address
            }
    
    def get_zoning_info(self, zoning_type: str) -> Dict:
        """
        用途地域の詳細情報を取得
        
        Args:
            zoning_type: 用途地域名
            
        Returns:
            用途地域の詳細情報
        """
        zoning_info = {
            '第一種低層住居専用地域': {
                'description': '低層住宅の良好な住環境を保護する地域',
                'building_height_limit': '10mまたは12m',
                'floor_area_ratio': '50%〜200%',
                'land_use_restrictions': '住宅、共同住宅、寄宿舎、下宿、小規模な店舗・事務所等'
            },
            '第二種低層住居専用地域': {
                'description': '主として低層住宅の良好な住環境を保護する地域',
                'building_height_limit': '10mまたは12m',
                'floor_area_ratio': '50%〜200%',
                'land_use_restrictions': '第一種低層住居専用地域の用途に加え、小規模な店舗・事務所等'
            },
            '第一種中高層住居専用地域': {
                'description': '中高層住宅の良好な住環境を保護する地域',
                'building_height_limit': '15m',
                'floor_area_ratio': '100%〜300%',
                'land_use_restrictions': '住宅、共同住宅、寄宿舎、下宿、店舗・事務所等'
            },
            '第二種中高層住居専用地域': {
                'description': '主として中高層住宅の良好な住環境を保護する地域',
                'building_height_limit': '15m',
                'floor_area_ratio': '100%〜300%',
                'land_use_restrictions': '第一種中高層住居専用地域の用途に加え、店舗・事務所等'
            },
            '第一種住居地域': {
                'description': '住居の環境を保護するための地域',
                'building_height_limit': '20m',
                'floor_area_ratio': '200%〜400%',
                'land_use_restrictions': '住宅、共同住宅、寄宿舎、下宿、店舗・事務所、ホテル・旅館等'
            },
            '第二種住居地域': {
                'description': '主として住居の環境を保護するための地域',
                'building_height_limit': '20m',
                'floor_area_ratio': '200%〜400%',
                'land_use_restrictions': '第一種住居地域の用途に加え、店舗・事務所、ホテル・旅館等'
            },
            '準住居地域': {
                'description': '道路の沿道において、自動車関連施設と調和した住居の環境を保護する地域',
                'building_height_limit': '20m',
                'floor_area_ratio': '200%〜400%',
                'land_use_restrictions': '住居地域の用途に加え、自動車関連施設等'
            },
            '近隣商業地域': {
                'description': '近隣の住民が日用品の買物をする店舗等の業務の利便の増進を図る地域',
                'building_height_limit': '20m',
                'floor_area_ratio': '200%〜400%',
                'land_use_restrictions': '店舗・事務所、ホテル・旅館、住宅等'
            },
            '商業地域': {
                'description': '主として商業その他の業務の利便の増進を図る地域',
                'building_height_limit': '制限なし',
                'floor_area_ratio': '制限なし',
                'land_use_restrictions': '店舗・事務所、ホテル・旅館、住宅等'
            },
            '準工業地域': {
                'description': '主として軽工業の環境を保護する地域',
                'building_height_limit': '20m',
                'floor_area_ratio': '200%〜400%',
                'land_use_restrictions': '工場、店舗・事務所、ホテル・旅館、住宅等'
            },
            '工業地域': {
                'description': '主として工業の業務の利便の増進を図る地域',
                'building_height_limit': '制限なし',
                'floor_area_ratio': '制限なし',
                'land_use_restrictions': '工場、店舗・事務所、住宅等'
            },
            '工業専用地域': {
                'description': '工業の業務の利便の増進を図る地域',
                'building_height_limit': '制限なし',
                'floor_area_ratio': '制限なし',
                'land_use_restrictions': '工場のみ'
            }
        }
        
        return zoning_info.get(zoning_type, {
            'description': '用途地域の詳細情報がありません',
            'building_height_limit': '不明',
            'floor_area_ratio': '不明',
            'land_use_restrictions': '不明'
        })
    
    def get_available_prefectures(self) -> List[str]:
        """
        利用可能な都道府県のリストを取得
        
        Returns:
            都道府県名のリスト
        """
        return list(self.geojson_files.keys())
    
    def get_file_info(self) -> Dict:
        """
        GeoJSONファイルの情報を取得
        
        Returns:
            ファイル情報の辞書
        """
        info = {}
        
        for prefecture, files in self.geojson_files.items():
            info[prefecture] = {
                'file_count': len(files),
                'files': files
            }
        
        return info


def create_zoning_checker(data_dir: str = "data") -> ZoningChecker:
    """
    用途地域チェッカーを作成する
    
    Args:
        data_dir: GeoJSONファイルが格納されているディレクトリ
        
    Returns:
        ZoningCheckerインスタンス
    """
    return ZoningChecker(data_dir)

