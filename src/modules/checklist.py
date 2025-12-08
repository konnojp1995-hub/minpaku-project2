"""
チェックリストモジュール
消防法・建築基準法・接道義務等の留意点をチェックリスト形式で管理する機能を提供
"""
import json
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .utils import log_error, log_info, load_rules


class ChecklistManager:
    """チェックリストを管理するクラス"""
    
    def __init__(self, rules_file: str = "rules.json"):
        """
        初期化
        
        Args:
            rules_file: ルールファイルのパス
        """
        self.rules_file = rules_file
        self.rules = load_rules()
        self.checklist_state = {}
    
    def get_building_standards_checklist(self) -> Dict:
        """
        建築基準法のチェックリストを取得
        
        Returns:
            建築基準法チェックリストの辞書
        """
        try:
            if not self.rules or 'building_standards' not in self.rules:
                return {
                    'success': False,
                    'error': '建築基準法の要件情報が読み込めませんでした',
                    'checklist': []
                }
            
            standards = self.rules['building_standards']
            checklist = []
            
            for standard_name, standard_info in standards.items():
                checklist_item = {
                    'id': standard_name,
                    'title': standard_name,
                    'description': standard_info.get('description', ''),
                    'required': standard_info.get('required', False),
                    'check_items': standard_info.get('check_items', []),
                    'checked': False,
                    'notes': ''
                }
                checklist.append(checklist_item)
            
            return {
                'success': True,
                'checklist': checklist,
                'category': '建築基準法'
            }
            
        except Exception as e:
            log_error(f"建築基準法チェックリスト取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"チェックリスト取得エラー: {str(e)}",
                'checklist': []
            }
    
    def get_minpaku_requirements_checklist(self) -> Dict:
        """
        民泊新法の要件チェックリストを取得
        
        Returns:
            民泊新法要件チェックリストの辞書
        """
        try:
            if not self.rules or 'minpaku_requirements' not in self.rules:
                return {
                    'success': False,
                    'error': '民泊新法の要件情報が読み込めませんでした',
                    'checklist': []
                }
            
            requirements = self.rules['minpaku_requirements']
            checklist = []
            
            for req_name, req_info in requirements.items():
                if isinstance(req_info, dict) and 'check_items' in req_info:
                    checklist_item = {
                        'id': req_name,
                        'title': req_name,
                        'description': req_info.get('description', ''),
                        'required': req_info.get('required', False),
                        'check_items': req_info.get('check_items', []),
                        'checked': False,
                        'notes': ''
                    }
                    checklist.append(checklist_item)
                elif isinstance(req_info, (int, str)):
                    # 数値や文字列の要件（宿泊者数制限など）
                    checklist_item = {
                        'id': req_name,
                        'title': req_name,
                        'description': f"{req_name}: {req_info}",
                        'required': True,
                        'check_items': [f"{req_name}の確認"],
                        'checked': False,
                        'notes': ''
                    }
                    checklist.append(checklist_item)
            
            return {
                'success': True,
                'checklist': checklist,
                'category': '民泊新法'
            }
            
        except Exception as e:
            log_error(f"民泊新法要件チェックリスト取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"チェックリスト取得エラー: {str(e)}",
                'checklist': []
            }
    
    def get_all_checklists(self) -> Dict:
        """
        すべてのチェックリストを取得
        
        Returns:
            全チェックリストの辞書
        """
        try:
            building_checklist = self.get_building_standards_checklist()
            minpaku_checklist = self.get_minpaku_requirements_checklist()
            
            all_checklists = []
            
            if building_checklist['success']:
                all_checklists.extend(building_checklist['checklist'])
            
            if minpaku_checklist['success']:
                all_checklists.extend(minpaku_checklist['checklist'])
            
            return {
                'success': True,
                'checklists': all_checklists,
                'total_items': len(all_checklists),
                'required_items': len([item for item in all_checklists if item.get('required', False)])
            }
            
        except Exception as e:
            log_error(f"全チェックリスト取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"チェックリスト取得エラー: {str(e)}",
                'checklists': []
            }
    
    def update_checklist_item(self, item_id: str, checked: bool, notes: str = "") -> bool:
        """
        チェックリスト項目の状態を更新
        
        Args:
            item_id: 項目ID
            checked: チェック状態
            notes: 備考
            
        Returns:
            更新成功の場合True
        """
        try:
            if item_id not in self.checklist_state:
                self.checklist_state[item_id] = {}
            
            self.checklist_state[item_id]['checked'] = checked
            self.checklist_state[item_id]['notes'] = notes
            
            return True
            
        except Exception as e:
            log_error(f"チェックリスト項目更新でエラー: {str(e)}")
            return False
    
    def get_checklist_progress(self) -> Dict:
        """
        チェックリストの進捗状況を取得
        
        Returns:
            進捗状況の辞書
        """
        try:
            all_checklists = self.get_all_checklists()
            
            if not all_checklists['success']:
                return {
                    'success': False,
                    'error': all_checklists['error']
                }
            
            total_items = all_checklists['total_items']
            checked_items = 0
            required_items = all_checklists['required_items']
            required_checked = 0
            
            for item in all_checklists['checklists']:
                item_id = item['id']
                if item_id in self.checklist_state:
                    if self.checklist_state[item_id].get('checked', False):
                        checked_items += 1
                        if item.get('required', False):
                            required_checked += 1
            
            progress_percentage = (checked_items / total_items * 100) if total_items > 0 else 0
            required_progress = (required_checked / required_items * 100) if required_items > 0 else 0
            
            return {
                'success': True,
                'total_items': total_items,
                'checked_items': checked_items,
                'progress_percentage': progress_percentage,
                'required_items': required_items,
                'required_checked': required_checked,
                'required_progress': required_progress,
                'is_complete': checked_items == total_items,
                'required_complete': required_checked == required_items
            }
            
        except Exception as e:
            log_error(f"チェックリスト進捗取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"進捗取得エラー: {str(e)}"
            }
    
    def get_checklist_summary(self) -> Dict:
        """
        チェックリストのサマリーを取得
        
        Returns:
            サマリーの辞書
        """
        try:
            progress = self.get_checklist_progress()
            
            if not progress['success']:
                return progress
            
            # カテゴリ別の進捗
            building_checklist = self.get_building_standards_checklist()
            minpaku_checklist = self.get_minpaku_requirements_checklist()
            
            categories = {}
            
            if building_checklist['success']:
                building_checked = 0
                for item in building_checklist['checklist']:
                    if self.checklist_state.get(item['id'], {}).get('checked', False):
                        building_checked += 1
                
                categories['建築基準法'] = {
                    'total': len(building_checklist['checklist']),
                    'checked': building_checked,
                    'progress': (building_checked / len(building_checklist['checklist']) * 100) if building_checklist['checklist'] else 0
                }
            
            if minpaku_checklist['success']:
                minpaku_checked = 0
                for item in minpaku_checklist['checklist']:
                    if self.checklist_state.get(item['id'], {}).get('checked', False):
                        minpaku_checked += 1
                
                categories['民泊新法'] = {
                    'total': len(minpaku_checklist['checklist']),
                    'checked': minpaku_checked,
                    'progress': (minpaku_checked / len(minpaku_checklist['checklist']) * 100) if minpaku_checklist['checklist'] else 0
                }
            
            return {
                'success': True,
                'overall_progress': progress,
                'categories': categories,
                'recommendations': self._generate_recommendations(progress)
            }
            
        except Exception as e:
            log_error(f"チェックリストサマリー取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"サマリー取得エラー: {str(e)}"
            }
    
    def _generate_recommendations(self, progress: Dict) -> List[str]:
        """
        進捗状況に基づいて推奨事項を生成
        
        Args:
            progress: 進捗状況の辞書
            
        Returns:
            推奨事項のリスト
        """
        recommendations = []
        
        if progress['required_progress'] < 100:
            recommendations.append("必須項目の確認を完了してください。")
        
        if progress['progress_percentage'] < 50:
            recommendations.append("チェックリストの進捗が遅れています。優先度の高い項目から確認してください。")
        
        if progress['required_complete'] and progress['progress_percentage'] < 100:
            recommendations.append("必須項目は完了していますが、推奨項目も確認することをお勧めします。")
        
        if progress['is_complete']:
            recommendations.append("すべてのチェック項目が完了しました。次のステップに進んでください。")
        
        return recommendations
    
    def export_checklist_state(self) -> Dict:
        """
        チェックリストの状態をエクスポート
        
        Returns:
            チェックリスト状態の辞書
        """
        try:
            all_checklists = self.get_all_checklists()
            
            if not all_checklists['success']:
                return {
                    'success': False,
                    'error': all_checklists['error']
                }
            
            export_data = {
                'checklist_state': self.checklist_state,
                'checklists': all_checklists['checklists'],
                'progress': self.get_checklist_progress(),
                'summary': self.get_checklist_summary()
            }
            
            return {
                'success': True,
                'export_data': export_data
            }
            
        except Exception as e:
            log_error(f"チェックリスト状態エクスポートでエラー: {str(e)}")
            return {
                'success': False,
                'error': f"エクスポートエラー: {str(e)}"
            }
    
    def import_checklist_state(self, import_data: Dict) -> bool:
        """
        チェックリストの状態をインポート
        
        Args:
            import_data: インポートするデータ
            
        Returns:
            インポート成功の場合True
        """
        try:
            if 'checklist_state' in import_data:
                self.checklist_state = import_data['checklist_state']
                return True
            else:
                return False
                
        except Exception as e:
            log_error(f"チェックリスト状態インポートでエラー: {str(e)}")
            return False
    
    def reset_checklist(self) -> bool:
        """
        チェックリストの状態をリセット
        
        Returns:
            リセット成功の場合True
        """
        try:
            self.checklist_state = {}
            return True
            
        except Exception as e:
            log_error(f"チェックリストリセットでエラー: {str(e)}")
            return False
    
    def get_item_status(self, item_id: str) -> Dict:
        """
        特定の項目の状態を取得
        
        Args:
            item_id: 項目ID
            
        Returns:
            項目状態の辞書
        """
        try:
            if item_id in self.checklist_state:
                return {
                    'success': True,
                    'checked': self.checklist_state[item_id].get('checked', False),
                    'notes': self.checklist_state[item_id].get('notes', '')
                }
            else:
                return {
                    'success': True,
                    'checked': False,
                    'notes': ''
                }
                
        except Exception as e:
            log_error(f"項目状態取得でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"状態取得エラー: {str(e)}"
            }


def create_checklist_manager(rules_file: str = "rules.json") -> ChecklistManager:
    """
    チェックリストマネージャーを作成する
    
    Args:
        rules_file: ルールファイルのパス
        
    Returns:
        ChecklistManagerインスタンス
    """
    return ChecklistManager(rules_file)

