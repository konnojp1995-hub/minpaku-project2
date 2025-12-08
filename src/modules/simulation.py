"""
投資回収シミュレーションモジュール
稼働率別の投資回収シミュレーションを行う機能を提供
"""
import pandas as pd
from typing import Dict, List
from .utils import log_error, log_info


class InvestmentSimulator:
    """投資回収シミュレーションを行うクラス"""
    
    def __init__(self):
        """初期化"""
        self.default_costs = {
            'initial_costs': {
                'deposit': 0,                    # 敷金
                'key_money': 0,                  # 礼金
                'brokerage_fee': 0,              # 仲介手数料
                'guarantee_company': 0,          # 保証会社
                'fire_insurance': 0,             # 火災保険
                'fire_equipment': 0,             # 消防設備
                'furniture': 0,                  # 家具・家電購入費用
                'renovation': 0,                 # リノベーション費用
                'license_fee': 0                 # 許可・届出費用
            },
            'operating_costs': {
                'rent': 0,                      # 家賃（月額）
                'utilities': 0,                # 水道光熱費（月額）
                'communication': 5000,          # 通信費（月額、デフォルト¥5,000）
                'insurance': 5000,             # 保険費（月額、デフォルト¥5,000）
                'cleaning': 0,                 # 清掃費（月額）
                'supplies': 0,                 # 消耗品（月額）
                'commission_rate': 0.15        # 手数料率（デフォルト15%）
            }
        }
        
        self.default_rates = {
            'occupancy_rates': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],  # 稼働率
            'daily_rate': 15000,                # 1泊あたりの単価
            'tax_rate': 0.1                     # 税率
        }
    
    def calculate_initial_investment(self, costs: Dict = None) -> Dict:
        """
        初期投資額を計算
        
        Args:
            costs: 費用の辞書（省略時はデフォルト値を使用）
            
        Returns:
            初期投資額の計算結果
        """
        try:
            if costs is None:
                costs = self.default_costs['initial_costs']
            
            total_initial = sum(costs.values())
            
            return {
                'success': True,
                'costs': costs,
                'total': total_initial,
                'breakdown': {
                    'deposit': costs.get('deposit', 0),
                    'key_money': costs.get('key_money', 0),
                    'brokerage_fee': costs.get('brokerage_fee', 0),
                    'guarantee_company': costs.get('guarantee_company', 0),
                    'fire_insurance': costs.get('fire_insurance', 0),
                    'fire_equipment': costs.get('fire_equipment', 0),
                    'furniture': costs.get('furniture', 0),
                    'renovation': costs.get('renovation', 0),
                    'license_fee': costs.get('license_fee', 0)
                }
            }
            
        except Exception as e:
            log_error(f"初期投資額計算でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"計算エラー: {str(e)}"
            }
    
    def calculate_annual_operating_costs(self, costs: Dict = None) -> Dict:
        """
        年間運用費用を計算
        
        Args:
            costs: 費用の辞書（省略時はデフォルト値を使用）
            
        Returns:
            年間運用費用の計算結果
        """
        try:
            if costs is None:
                costs = self.default_costs['operating_costs']
            
            # 月額費用を年間に変換（commission_rateは収益から差し引くため除外）
            monthly_costs = sum(v for k, v in costs.items() if k != 'commission_rate')
            annual_costs = monthly_costs * 12
            
            return {
                'success': True,
                'monthly_costs': costs,
                'annual_costs': annual_costs,
                'breakdown': {
                    'rent': costs.get('rent', 0) * 12,
                    'utilities': costs.get('utilities', 0) * 12,
                    'communication': costs.get('communication', 0) * 12,
                    'insurance': costs.get('insurance', 0) * 12,
                    'cleaning': costs.get('cleaning', 0) * 12,
                    'supplies': costs.get('supplies', 0) * 12
                    # 手数料は収益から差し引くため、ここには含めない
                }
            }
            
        except Exception as e:
            log_error(f"年間運用費用計算でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"計算エラー: {str(e)}"
            }
    
    def calculate_annual_revenue(self, daily_rate: float, occupancy_rate: float, commission_rate: float = 0.15) -> Dict:
        """
        年間収益を計算（手数料を差し引いた後）
        
        Args:
            daily_rate: 1泊あたりの単価
            occupancy_rate: 稼働率
            commission_rate: 手数料率（デフォルト15%）
            
        Returns:
            年間収益の計算結果
        """
        try:
            # 実際の営業日数は年間365日のうち何%稼働するかで計算
            # 旅館業を申請するケースも想定するため、180日の制限は設けない
            # 民泊新法の場合は50%の値（182.5日）を自分で読み取る
            actual_operating_days = 365 * occupancy_rate
            
            # 年間総収益（手数料前）
            gross_annual_revenue = daily_rate * actual_operating_days
            
            # 手数料を差し引く
            commission_amount = gross_annual_revenue * commission_rate
            annual_revenue = gross_annual_revenue - commission_amount
            
            return {
                'success': True,
                'daily_rate': daily_rate,
                'occupancy_rate': occupancy_rate,
                'max_operating_days': 365,  # 年間365日（旅館業も想定）
                'actual_operating_days': actual_operating_days,
                'gross_annual_revenue': gross_annual_revenue,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'annual_revenue': annual_revenue
            }
            
        except Exception as e:
            log_error(f"年間収益計算でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"計算エラー: {str(e)}"
            }
    
    def calculate_profit_loss(self, initial_investment: float, annual_revenue: float, 
                            annual_costs: float, tax_rate: float = 0.1) -> Dict:
        """
        損益を計算
        
        Args:
            initial_investment: 初期投資額
            annual_revenue: 年間収益
            annual_costs: 年間費用
            tax_rate: 税率
            
        Returns:
            損益計算結果
        """
        try:
            # 税引前利益
            gross_profit = annual_revenue - annual_costs
            
            # 税金
            tax = gross_profit * tax_rate if gross_profit > 0 else 0
            
            # 税引後利益
            net_profit = gross_profit - tax
            
            # 投資回収年数
            payback_years = initial_investment / net_profit if net_profit > 0 else float('inf')
            
            return {
                'success': True,
                'gross_profit': gross_profit,
                'tax': tax,
                'net_profit': net_profit,
                'payback_years': payback_years,
                'annual_revenue': annual_revenue,
                'annual_costs': annual_costs,
                'initial_investment': initial_investment
            }
            
        except Exception as e:
            log_error(f"損益計算でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"計算エラー: {str(e)}"
            }
    
    def run_simulation(self, initial_costs: Dict = None, operating_costs: Dict = None,
                      daily_rate: float = None, occupancy_rates: List[float] = None,
                      tax_rate: float = None, commission_rate: float = None) -> Dict:
        """
        投資回収シミュレーションを実行
        
        Args:
            initial_costs: 初期費用
            operating_costs: 運用費用
            daily_rate: 1泊あたりの単価
            occupancy_rates: 稼働率のリスト
            tax_rate: 税率
            commission_rate: 手数料率
            
        Returns:
            シミュレーション結果
        """
        try:
            log_info("投資回収シミュレーションを開始")
            
            # デフォルト値の設定
            if initial_costs is None:
                initial_costs = self.default_costs['initial_costs']
            if operating_costs is None:
                operating_costs = self.default_costs['operating_costs']
            if daily_rate is None:
                daily_rate = self.default_rates['daily_rate']
            if occupancy_rates is None:
                occupancy_rates = self.default_rates['occupancy_rates']
            if tax_rate is None:
                tax_rate = self.default_rates['tax_rate']
            if commission_rate is None:
                commission_rate = operating_costs.get('commission_rate', 0.15)
            
            # 初期投資額を計算
            initial_result = self.calculate_initial_investment(initial_costs)
            if not initial_result['success']:
                return initial_result
            
            # 年間運用費用を計算
            operating_result = self.calculate_annual_operating_costs(operating_costs)
            if not operating_result['success']:
                return operating_result
            
            # 各稼働率でのシミュレーション結果
            simulation_results = []
            
            for occupancy_rate in occupancy_rates:
                # 年間収益を計算（手数料を差し引いた後）
                revenue_result = self.calculate_annual_revenue(daily_rate, occupancy_rate, commission_rate)
                if not revenue_result['success']:
                    continue
                
                # 損益を計算
                profit_result = self.calculate_profit_loss(
                    initial_result['total'],
                    revenue_result['annual_revenue'],
                    operating_result['annual_costs'],
                    tax_rate
                )
                
                if profit_result['success']:
                    simulation_results.append({
                        'occupancy_rate': occupancy_rate,
                        'annual_revenue': revenue_result['annual_revenue'],
                        'annual_costs': operating_result['annual_costs'],
                        'gross_profit': profit_result['gross_profit'],
                        'tax': profit_result['tax'],
                        'net_profit': profit_result['net_profit'],
                        'payback_years': profit_result['payback_years'],
                        'actual_operating_days': revenue_result['actual_operating_days']
                    })
            
            # 損益分岐点を計算
            breakeven_rate = self._calculate_breakeven_rate(
                initial_result['total'],
                operating_result['annual_costs'],
                daily_rate,
                tax_rate
            )
            
            return {
                'success': True,
                'initial_investment': initial_result,
                'annual_operating_costs': operating_result,
                'simulation_results': simulation_results,
                'breakeven_rate': breakeven_rate,
                'parameters': {
                    'daily_rate': daily_rate,
                    'tax_rate': tax_rate,
                    'occupancy_rates': occupancy_rates
                }
            }
            
        except Exception as e:
            log_error(f"シミュレーション実行でエラー: {str(e)}")
            return {
                'success': False,
                'error': f"シミュレーションエラー: {str(e)}"
            }
    
    def _calculate_breakeven_rate(self, initial_investment: float, annual_costs: float,
                                daily_rate: float, tax_rate: float) -> float:
        """
        損益分岐点の稼働率を計算
        
        Args:
            initial_investment: 初期投資額
            annual_costs: 年間費用
            daily_rate: 1泊あたりの単価
            tax_rate: 税率
            
        Returns:
            損益分岐点の稼働率
        """
        try:
            # 税引後利益が0になる稼働率を計算
            # net_profit = (daily_rate * operating_days - annual_costs) * (1 - tax_rate) = 0
            # operating_days = annual_costs / daily_rate
            # occupancy_rate = operating_days / 365（年間365日のうち何%稼働するか）
            
            operating_days = annual_costs / daily_rate
            occupancy_rate = operating_days / 365
            
            return min(occupancy_rate, 1.0)  # 最大100%
            
        except Exception as e:
            log_error(f"損益分岐点計算でエラー: {str(e)}")
            return 0.0
    
    def create_simulation_dataframe(self, simulation_results: List[Dict]) -> pd.DataFrame:
        """
        シミュレーション結果をDataFrameに変換
        
        Args:
            simulation_results: シミュレーション結果のリスト
            
        Returns:
            シミュレーション結果のDataFrame
        """
        try:
            if not simulation_results:
                return pd.DataFrame()
            
            df = pd.DataFrame(simulation_results)
            
            # 列の順序を整理
            columns_order = [
                'occupancy_rate',
                'actual_operating_days',
                'annual_revenue',
                'annual_costs',
                'gross_profit',
                'tax',
                'net_profit',
                'payback_years'
            ]
            
            df = df[columns_order]
            
            # 列名を日本語に変更
            df = df.rename(columns={
                'occupancy_rate': '稼働率',
                'actual_operating_days': '実際の営業日数',
                'annual_revenue': '年間収益',
                'annual_costs': '年間費用',
                'gross_profit': '税引前利益',
                'tax': '税金',
                'net_profit': '税引後利益',
                'payback_years': '投資回収年数'
            })
            
            # 数値をフォーマット
            df['稼働率'] = df['稼働率'].apply(lambda x: f"{x:.1%}")
            # 実際の営業日数は整数に丸める（浮動小数点誤差を避けるため）
            df['実際の営業日数'] = df['実際の営業日数'].apply(lambda x: f"{round(x):.0f}日")
            df['年間収益'] = df['年間収益'].apply(lambda x: f"¥{x:,.0f}")
            df['年間費用'] = df['年間費用'].apply(lambda x: f"¥{x:,.0f}")
            df['税引前利益'] = df['税引前利益'].apply(lambda x: f"¥{x:,.0f}")
            df['税金'] = df['税金'].apply(lambda x: f"¥{x:,.0f}")
            df['税引後利益'] = df['税引後利益'].apply(lambda x: f"¥{x:,.0f}")
            df['投資回収年数'] = df['投資回収年数'].apply(lambda x: f"{x:.1f}年" if x != float('inf') else "回収不可")
            
            return df
            
        except Exception as e:
            log_error(f"DataFrame作成でエラー: {str(e)}")
            return pd.DataFrame()
    
    def get_recommendations(self, simulation_results: List[Dict]) -> List[str]:
        """
        シミュレーション結果に基づいて推奨事項を生成
        
        Args:
            simulation_results: シミュレーション結果のリスト
            
        Returns:
            推奨事項のリスト
        """
        try:
            recommendations = []
            
            if not simulation_results:
                return ["シミュレーション結果がありません。"]
            
            # 最も収益性の高い稼働率を特定
            best_result = max(simulation_results, key=lambda x: x['net_profit'])
            best_rate = best_result['occupancy_rate']
            
            recommendations.append(f"最も収益性の高い稼働率は{best_rate:.1%}です。")
            
            # 投資回収年数の分析
            payback_years = [r['payback_years'] for r in simulation_results if r['payback_years'] != float('inf')]
            
            if payback_years:
                min_payback = min(payback_years)
                recommendations.append(f"最短投資回収年数は{min_payback:.1f}年です。")
                
                if min_payback > 10:
                    recommendations.append("投資回収年数が長いため、初期投資額の見直しを検討してください。")
                elif min_payback < 5:
                    recommendations.append("投資回収年数が短く、収益性が高いです。")
            
            # 損益分岐点の分析
            profitable_results = [r for r in simulation_results if r['net_profit'] > 0]
            
            if len(profitable_results) < len(simulation_results) / 2:
                recommendations.append("多くの稼働率で赤字となる可能性があります。単価の見直しを検討してください。")
            
            return recommendations
            
        except Exception as e:
            log_error(f"推奨事項生成でエラー: {str(e)}")
            return ["推奨事項の生成に失敗しました。"]


def create_investment_simulator() -> InvestmentSimulator:
    """
    投資シミュレーターを作成する
    
    Returns:
        InvestmentSimulatorインスタンス
    """
    return InvestmentSimulator()

