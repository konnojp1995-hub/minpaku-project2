"""
民泊開業検討者向けチャットボットツール
メインのStreamlit UI
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import sys
import re
from typing import Dict
from datetime import datetime

# モジュールのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.utils import load_env_config, log_error, log_info, log_success, log_warning
from modules.ocr_extractor import create_ocr_extractor
from modules.geocoder import create_geocoder
from modules.zoning_checker import create_zoning_checker
from modules.law_checker import create_law_checker
from modules.simulation import create_investment_simulator
from modules.law_result_formatter import format_law_check_results
from modules.airbnb_price_estimator import create_airbnb_price_estimator
from modules.initial_cost_estimator import create_initial_cost_estimator
from modules.profiler import time_block


def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="民泊開業検討ツール",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # タイトル
    st.title("🏠 民泊開業検討ツール")
    st.markdown("物件の適法性・採算性をワンストップで確認できるチャットボットツール")
    
    # 環境設定を読み込み
    config = load_env_config()
    st.session_state['config'] = config
    
    # サイドバー（チャット履歴と設定のタブ）
    with st.sidebar:
        sidebar_tab1, sidebar_tab2 = st.tabs(["💬 チャット履歴", "⚙️ 設定"])
        
        with sidebar_tab1:
            _render_chat_history_sidebar()
        
        with sidebar_tab2:
            st.header("⚙️ 設定")
            
            # API設定
            st.subheader("API設定")
            google_maps_api_key = st.text_input(
                "Google Maps API Key",
                value=config.get('google_maps_api_key', ''),
                type="password",
                help="ジオコーディングに使用（オプション）"
            )
            
            gemini_api_key = st.text_input(
                "Gemini API Key",
                value=config.get('gemini_api_key', ''),
                type="password",
                help="Gemini OCR機能に使用（オプション）"
            )

            # 入力値をセッションへ保存（後段処理で利用）
            st.session_state['gemini_api_key'] = gemini_api_key
            st.session_state['google_maps_api_key'] = google_maps_api_key
            
            # OCR設定（Geminiのみ使用）
            st.subheader("OCR設定")
            st.info("📌 Gemini OCRを使用します（最高精度）")
            
            # Gemini OCRの設定
            if gemini_api_key:
                st.success("✅ Gemini APIキーが設定されています（Gemini OCR機能が利用可能）")
            else:
                st.error("❌ Gemini APIキーが設定されていません。住所抽出機能を使用するにはGemini APIキーの設定が必要です。")

            # ファイル設定
            st.subheader("ファイル設定")
            max_file_size = st.number_input(
                "最大ファイルサイズ (MB)",
                min_value=1,
                max_value=100,
                value=config.get('max_file_size_mb', 10),
                help="アップロード可能なファイルの最大サイズ"
            )
    
    # メインコンテンツ
    tab_chat, tab_simulation = st.tabs([
        "🤖 AIアシスタント", "💰 投資シミュレーション"
    ])
    
    with tab_chat:
        chat_bot_tab()
    
    with tab_simulation:
        simulation_tab()


def suggest_next_action(zoning_type: str, minpaku_result: Dict, ryokan_result: Dict, tokku_result: Dict,
                         fire_result: Dict, building_result: Dict, local_result: Dict,
                         law_checker=None) -> str:
    """
    次のアクションを提案する（法令判定の結果に基づきGeminiで動的生成）
    
    Args:
        zoning_type: 用途地域
        minpaku_result: 民泊新法の判定結果
        ryokan_result: 旅館業の判定結果
        tokku_result: 特区民泊の判定結果
        fire_result: 消防法上の要件
        building_result: 建築基準法上の要件
        local_result: 自治体の制限
        law_checker: LawCheckerインスタンス（Gemini API呼び出し用）
        
    Returns:
        アクション提案のテキスト
    """
    from modules.law_result_formatter import parse_permission_result, parse_requirements
    
    # Geminiが利用できない場合は簡易版を返す
    if not law_checker or not law_checker.gemini_available:
        return _generate_fallback_suggestions(zoning_type, minpaku_result, ryokan_result, tokku_result,
                                            fire_result, building_result, local_result)
    
    # 判定結果を整理
    results_summary = []
    
    # 用途地域
    results_summary.append(f"用途地域: {zoning_type if zoning_type and zoning_type != '不明' else '不明'}")
    
    # 民泊新法の判定結果
    if minpaku_result.get('success'):
        permission_text = minpaku_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        results_summary.append(f"民泊新法 - 許可判定: {formatted.get('判定', '判定不可')}")
        results_summary.append(f"民泊新法 - 主な理由: {formatted.get('理由', '不明')}")
        results_summary.append(f"民泊新法 - その他制限: {formatted.get('制限', '特になし')}")
    else:
        results_summary.append("民泊新法 - 判定結果: 判定不可")
    
    # 旅館業法の判定結果
    if ryokan_result.get('success'):
        permission_text = ryokan_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        results_summary.append(f"旅館業法 - 許可判定: {formatted.get('判定', '判定不可')}")
        results_summary.append(f"旅館業法 - 主な理由: {formatted.get('理由', '不明')}")
        results_summary.append(f"旅館業法 - その他制限: {formatted.get('制限', '特になし')}")
    else:
        results_summary.append("旅館業法 - 判定結果: 判定不可")
    
    # 特区民泊の判定結果
    if tokku_result.get('success'):
        permission_text = tokku_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        results_summary.append(f"特区民泊 - 許可判定: {formatted.get('判定', '判定不可')}")
        results_summary.append(f"特区民泊 - 主な理由: {formatted.get('理由', '不明')}")
        results_summary.append(f"特区民泊 - その他制限: {formatted.get('制限', '特になし')}")
    else:
        results_summary.append("特区民泊 - 判定結果: 判定不可")
    
    # 消防法上の要件
    if fire_result.get('success'):
        requirements_text = fire_result.get('requirements', '')
        formatted = parse_requirements(requirements_text, ['火災報知器', '竪穴区画', 'その他留意点'])
        results_summary.append(f"消防法 - 火災報知器: {formatted.get('火災報知器', '不明')}")
        results_summary.append(f"消防法 - 竪穴区画: {formatted.get('竪穴区画', '不明')}")
        results_summary.append(f"消防法 - その他留意点: {formatted.get('その他留意点', '特になし')}")
    else:
        results_summary.append("消防法 - 判定結果: 判定不可")
    
    # 建築基準法上の要件
    if building_result.get('success'):
        requirements_text = building_result.get('requirements', '')
        formatted = parse_requirements(requirements_text, ['用途変更', '竪穴区画', 'その他制限', '接道義務'])
        results_summary.append(f"建築基準法 - 用途変更: {formatted.get('用途変更', '不明')}")
        results_summary.append(f"建築基準法 - 竪穴区画: {formatted.get('竪穴区画', '不明')}")
        results_summary.append(f"建築基準法 - その他制限: {formatted.get('その他制限', '特になし')}")
        results_summary.append(f"建築基準法 - 接道義務: {formatted.get('接道義務', '不明')}")
    else:
        results_summary.append("建築基準法 - 判定結果: 判定不可")
    
    # 自治体の制限
    if local_result.get('success'):
        restrictions = local_result.get('restrictions', '特になし')
        results_summary.append(f"自治体の制限: {restrictions}")
    else:
        results_summary.append("自治体の制限: 特になし")
    
    # Geminiでアクションを生成
    prompt = f"""以下の法令判定結果を基に、民泊開業に向けた「次に取るべきアクション」を箇条書きで生成してください。

判定結果:
{chr(10).join(results_summary)}

重要な注意事項:
1. 判定結果と矛盾するアクションは絶対に出力しない
2. 各判定項目に基づいて具体的なアクションを生成する
   - 例：竪穴区画判定が「不要」なら「竪穴区画に関する工事は不要」と明記
   - 例：消火器判定が「必要」なら「消火器を設置してください」と明記
3. 各法令ごとにアクションを整理:
   - 民泊新法／旅館業法：手続き・届出・設備確認など
   - 消防法：火災報知器、消火器、竪穴区画、誘導灯など
   - 建築基準法：用途変更、竪穴区画、採光・換気、接道義務など
4. 推奨アクションとして、必要な手続き・設備・専門家相談などをまとめて提示
5. 表示形式は箇条書きで簡潔に（各項目は1〜2行程度）

出力形式（Markdown形式）:
- 見出しは **見出し名** 形式
- 箇条書きは各項目を独立した行で表示
- 見出しの後には空行を入れる

「次に取るべきアクション」を生成してください:"""
    
    try:
        response = law_checker._call_gemini(prompt)
        if response and response != "Gemini APIが利用できません" and not response.startswith("エラー"):
            return response
        else:
            # Geminiが失敗した場合はフォールバック
            return _generate_fallback_suggestions(zoning_type, minpaku_result, ryokan_result, tokku_result,
                                                fire_result, building_result, local_result)
    except Exception as e:
        # エラー時はフォールバック
        return _generate_fallback_suggestions(zoning_type, minpaku_result, ryokan_result, tokku_result,
                                            fire_result, building_result, local_result)


def _generate_fallback_suggestions(zoning_type: str, minpaku_result: Dict, ryokan_result: Dict, tokku_result: Dict,
                                   fire_result: Dict, building_result: Dict, local_result: Dict) -> str:
    """
    フォールバック用のアクション提案（Geminiが使えない場合）
    
    Args:
        zoning_type: 用途地域
        minpaku_result: 民泊新法の判定結果
        ryokan_result: 旅館業の判定結果
        tokku_result: 特区民泊の判定結果
        fire_result: 消防法上の要件
        building_result: 建築基準法上の要件
        local_result: 自治体の制限
        
    Returns:
        アクション提案のテキスト
    """
    from modules.law_result_formatter import parse_permission_result, parse_requirements
    
    suggestions = []
    
    # 用途地域の確認
    if not zoning_type or zoning_type == "不明":
        suggestions.append("**📍 優先**")
        suggestions.append("用途地域が判定できませんでした。住所を再確認してください。")
        suggestions.append("")
    
    # 判定結果に基づくアクション
    # 民泊新法
    if minpaku_result.get('success'):
        permission_text = minpaku_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        permission_status = formatted.get('判定', '')
        reason = formatted.get('理由', '不明')
        restrictions = formatted.get('制限', '特になし')
        
        if '許可' in permission_status and '不許可' not in permission_status:
            suggestions.append("✅ **民泊新法**")
            if '180日' in restrictions or '日数' in restrictions:
                suggestions.append("  許可可能。年間営業日数に制限があるため、収益計画を確認しましょう。")
            else:
                suggestions.append("  許可可能。手続きを進めましょう。")
            suggestions.append("")
            suggestions.append("  • 住宅宿泊事業届出の準備（管理者選任、宿泊者名簿等）")
            suggestions.append("  • 必要設備の確認・設置（火災報知器、消火器等）")
            suggestions.append("  • 近隣への説明・同意取得（推奨）")
        elif '条件' in permission_status or '条件' in reason:
            suggestions.append("⚠️ **民泊新法**")
            suggestions.append("  条件付きで許可可能。条件を確認し、遵守できるか検討しましょう。")
        else:
            suggestions.append("❌ **民泊新法**")
            suggestions.append(f"  許可困難。{reason if reason != '不明' else '用途地域や条例を確認してください。'}")
        suggestions.append("")
    
    # 旅館業法
    if ryokan_result.get('success'):
        permission_text = ryokan_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        permission_status = formatted.get('判定', '')
        reason = formatted.get('理由', '不明')
        
        if '許可' in permission_status and '不許可' not in permission_status:
            suggestions.append("✅ **旅館業法**")
            suggestions.append("  許可可能。営業日数制限なしですが、設備基準が厳格です。")
            suggestions.append("")
            suggestions.append("  • 旅館業許可申請の準備（保健所への申請）")
            suggestions.append("  • 構造基準・設備基準の確認と工事計画")
            suggestions.append("")
    
    # 特区民泊
    if tokku_result.get('success'):
        permission_text = tokku_result.get('permission', '')
        formatted = parse_permission_result(permission_text)
        permission_status = formatted.get('判定', '')
        
        if '許可' in permission_status and '不許可' not in permission_status:
            suggestions.append("✅ **特区民泊**")
            suggestions.append("  許可可能。該当地域の特区制度を確認してください。")
            suggestions.append("")
    
    # 消防法
    if fire_result.get('success'):
        requirements_text = fire_result.get('requirements', '')
        formatted = parse_requirements(requirements_text, ['火災報知器', '竪穴区画', 'その他留意点'])
        
        fire_detector = formatted.get('火災報知器', '不明')
        vertical_fire = formatted.get('竪穴区画', '不明')
        other_fire = formatted.get('その他留意点', '特になし')
        
        suggestions.append("🔥 **消防法**")
        if '要' in vertical_fire or '必要' in vertical_fire:
            suggestions.append("  • 竪穴区画工事が必要です。工事費用を確認しましょう。")
        elif '不要' in vertical_fire:
            suggestions.append("  • 竪穴区画に関する工事は不要です。")
        
        if '消火器' in other_fire or '設置' in other_fire:
            suggestions.append("  • 消火器を設置してください。")
        
        if '住宅用' in fire_detector:
            suggestions.append("  • 住宅用火災警報器で対応可能です。")
        suggestions.append("")
    
    # 建築基準法
    if building_result.get('success'):
        requirements_text = building_result.get('requirements', '')
        formatted = parse_requirements(requirements_text, ['用途変更', '竪穴区画', 'その他制限', '接道義務'])
        
        use_change = formatted.get('用途変更', '不明')
        building_vertical = formatted.get('竪穴区画', '不明')
        building_other = formatted.get('その他制限', '特になし')
        road_access = formatted.get('接道義務', '不明')
        
        suggestions.append("🏗️ **建築基準法**")
        if '要' in use_change and '不要' not in use_change:
            suggestions.append("  • 用途変更申請が必要です。行政への相談が必要です。")
        elif '不要' in use_change:
            suggestions.append("  • 用途変更申請は不要です。")
        
        if '要' in building_vertical and '不要' not in building_vertical:
            suggestions.append("  • 竪穴区画工事が必要です。")
        elif '不要' in building_vertical:
            suggestions.append("  • 竪穴区画に関する工事は不要です。")
        
        if '接道' in road_access and ('必要' in road_access or '義務' in road_access):
            suggestions.append("  • 接道要件を確認してください。旅館業申請時に必要です。")
        
        if '採光' in building_other or '換気' in building_other:
            suggestions.append("  • 採光・換気要件を確認してください。")
        suggestions.append("")
    
    # 自治体の制限
    if local_result.get('success'):
        restrictions = local_result.get('restrictions', '特になし')
        if restrictions != '特になし' and restrictions.strip():
            suggestions.append("📋 **自治体規制**")
            suggestions.append(f"  • {restrictions.strip()[:100]} 詳しくは自治体に確認してください。")
            suggestions.append("")
    
    # 推奨アクション
    suggestions.append("**📝 推奨アクション**")
    suggestions.append("")
    suggestions.append("  • 専門家への相談（行政書士：手続き、建築士：設備基準）")
    suggestions.append("  • 投資シミュレーションタブで収益性を確認")
    
    return "\n".join(suggestions)


def chat_bot_tab():
    """チャットボット形式の統合ページ"""
    st.header("🤖 民泊AIアシスタント")
    st.markdown("マイソク画像をアップロードすると、自動で住所抽出→用途地域判定→法令判定まで行います。")
    
    config = st.session_state.get('config', {})
    gemini_api_key = st.session_state.get('gemini_api_key', config.get('gemini_api_key', ''))
    google_maps_api_key = st.session_state.get('google_maps_api_key', config.get('google_maps_api_key', ''))
    
    # チャット履歴の初期化
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    # chat_stepの初期化（独立して初期化）
    if 'chat_step' not in st.session_state:
        st.session_state['chat_step'] = 'upload'  # upload, ocr, address, process, result
    
    # 初期メッセージを追加（初回のみ）
    if len(st.session_state['chat_history']) == 0:
        st.session_state['chat_history'].append({
            'role': 'assistant',
            'content': 'こんにちは！民泊開業の適法性を確認するAIアシスタントです。\nマイソク画像（不動産広告画像）をアップロードしてください。'
        })
    
    # チャット履歴の表示
    for msg in st.session_state['chat_history']:
        with st.chat_message(msg['role']):
            # 改行を適切に処理
            content = msg['content']
            if '\n' in content:
                # 複数行の場合は改行を保持
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if i == 0:
                        st.write(line)
                    else:
                        st.write(line)
            else:
                st.write(content)
            
            if 'data' in msg:
                for key, value in msg['data'].items():
                    st.write(f"**{key}**: {value}")
    
    # 画像アップロード
    uploaded_file = st.file_uploader(
        "マイソク画像をアップロード",
        type=["jpg", "jpeg", "png", "pdf"],
        key="chat_uploader"
    )
    
    # 画像表示と確認フロー
    if uploaded_file and st.session_state['chat_step'] == 'upload':
        if uploaded_file.type.startswith('image/'):
            image = Image.open(uploaded_file)
            with st.chat_message("assistant"):
                st.write("📷 アップロードされた画像を確認してください。")
                st.image(image, caption="アップロードされた画像")
                st.session_state['uploaded_image'] = image
        else:
            with st.chat_message("assistant"):
                st.write("📄 PDFファイルがアップロードされました。")
                st.session_state['uploaded_file_data'] = uploaded_file.getbuffer()
        
        st.session_state['uploaded_file'] = uploaded_file
        st.session_state['chat_step'] = 'confirm'
    
    # 画像確認後の実行確認
    if st.session_state['chat_step'] == 'confirm':
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ この画像で解析を実行", type="primary"):
                st.session_state['chat_step'] = 'ocr'
                st.rerun()
        with col2:
            if st.button("❌ キャンセル"):
                st.session_state['chat_step'] = 'upload'
                st.session_state['uploaded_file'] = None
                st.session_state['uploaded_image'] = None
                st.rerun()
    
    # ステップ1: OCR処理
    if st.session_state['chat_step'] == 'ocr':
        if not gemini_api_key:
            with st.chat_message("assistant"):
                st.error("❌ Gemini APIキーが設定されていません。サイドバーで設定してください。")
            st.session_state['chat_step'] = 'upload'
            return
        
        with st.chat_message("assistant"):
            st.write("📸 画像を解析中です...")
        
        # OCR処理
        try:
            uploaded_file = st.session_state.get('uploaded_file')
            if not uploaded_file:
                with st.chat_message("assistant"):
                    st.error("❌ 画像ファイルが見つかりません。")
                st.session_state['chat_step'] = 'upload'
                return
            
            ocr_extractor = create_ocr_extractor(gemini_api_key=gemini_api_key)
            if not ocr_extractor.gemini_available:
                err = getattr(ocr_extractor, 'gemini_init_error', '')
                with st.chat_message("assistant"):
                    st.error(f"❌ Gemini初期化に失敗しました: {err}")
                    if "Timeout" in err or "timeout" in err.lower():
                        st.info("💡 ネットワーク接続の問題が発生しています。しばらく待ってから再試行してください。")
                st.session_state['chat_step'] = 'upload'
                return
            
            # 画像を読み込み
            with time_block("OCR処理"):
                if uploaded_file.type.startswith('image/'):
                    image = st.session_state.get('uploaded_image')
                    if image is None:
                        image = Image.open(uploaded_file)
                    result = ocr_extractor.extract_from_pil_image(image)
                else:
                    # PDFの場合は一時ファイルに保存
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        file_data = st.session_state.get('uploaded_file_data')
                        if file_data:
                            tmp_file.write(file_data)
                        else:
                            tmp_file.write(uploaded_file.getbuffer())
                        temp_path = tmp_file.name
                    result = ocr_extractor.extract_from_image(temp_path)
                    os.unlink(temp_path)
            
            raw_texts = result.get('raw_texts', [])
            
            if result['success'] and result.get('addresses'):
                address = result['addresses'][0]
                
                st.session_state['extracted_address'] = address
                st.session_state['raw_texts'] = raw_texts
                st.session_state['chat_step'] = 'address'
                
                with st.chat_message("assistant"):
                    st.success("✅ 画像解析が完了しました！")
                    st.write("")
                    st.write(f"**抽出された住所**: {address}")
                    if raw_texts:
                        with st.expander("📝 抽出されたテキストを表示"):
                            for text in raw_texts:
                                st.text(text)
                
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': f'✅ 画像解析が完了しました！\n**抽出された住所**: {address}',
                    'data': {'抽出されたテキスト': '\n'.join(raw_texts[:3]) if raw_texts else 'なし'}
                })
            else:
                error_msg = result.get('error', '住所を抽出できませんでした')
                
                with st.chat_message("assistant"):
                    st.error(f"❌ {error_msg}")
                    
                    # 抽出されたテキストがある場合は表示
                    if raw_texts:
                        st.info("📝 以下のテキストが抽出されましたが、住所として認識できませんでした。")
                        with st.expander("抽出されたテキストを表示"):
                            for i, text in enumerate(raw_texts, 1):
                                st.text(f"[{i}] {text}")
                        
                        # 住所候補がある場合は表示
                        address_candidates = result.get('address_candidates', [])
                        if address_candidates:
                            st.write("")
                            st.warning(f"住所らしき候補を{len(address_candidates)}件発見しましたが、完全な住所として認識できませんでした。")
                            with st.expander("住所候補を表示"):
                                for i, candidate in enumerate(address_candidates, 1):
                                    st.text(f"[{i}] {candidate}")
                        
                        st.write("")
                        st.write("**対処方法:**")
                        st.write("- 画像が鮮明か確認してください")
                        st.write("- 住所部分が画像内に含まれているか確認してください")
                        st.write("- 手動で住所を入力することもできます")
                        
                        # 手動入力オプション
                        st.write("")
                        manual_address = st.text_input("住所を手動で入力してください", key="manual_address_input")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("手動入力した住所を使用", key="use_manual_address", type="primary"):
                                if manual_address:
                                    st.session_state['extracted_address'] = manual_address
                                    st.session_state['raw_texts'] = raw_texts
                                    st.session_state['chat_step'] = 'address'
                                    st.rerun()
                                else:
                                    st.warning("住所を入力してください。")
                        with col2:
                            if st.button("新しい画像をアップロード", key="retry_upload"):
                                st.session_state['chat_step'] = 'upload'
                                st.session_state['uploaded_file'] = None
                                st.session_state['uploaded_image'] = None
                                st.rerun()
                    else:
                        st.write("**対処方法:**")
                        st.write("- 画像が鮮明か確認してください")
                        st.write("- 画像からテキストが読み取れているか確認してください")
                        st.write("- 別の画像で再試行してください")
                        
                        st.write("")
                        if st.button("新しい画像をアップロード", key="retry_upload_no_text"):
                            st.session_state['chat_step'] = 'upload'
                            st.session_state['uploaded_file'] = None
                            st.session_state['uploaded_image'] = None
                            st.rerun()
                
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': f'❌ {error_msg}'
                })
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"❌ エラーが発生しました: {str(e)}")
    
    # ステップ2: 住所確認・修正
    if st.session_state['chat_step'] == 'address':
        with st.chat_message("assistant"):
            st.write("📍 以下の住所を確認・修正してください。")
        
        address_input = st.text_input(
            "住所",
            value=st.session_state.get('extracted_address', ''),
            key="address_input"
        )
        
        if st.button("住所を確定して続行", type="primary"):
            if address_input:
                st.session_state['selected_address'] = address_input
                st.session_state['chat_step'] = 'process'
                st.rerun()
            else:
                st.warning("住所を入力してください。")
    
    # ステップ3: 連続処理（ジオコーディング→用途地域→法令判定）
    if st.session_state['chat_step'] == 'process':
        with st.chat_message("assistant"):
            st.write("🔄 処理を実行中です...")
        
        progress_bar = st.progress(0)
        
        try:
            address = st.session_state.get('selected_address', '')
            
            # 画像解析結果を表示
            with st.chat_message("assistant"):
                st.write("")
                st.markdown("**📸 画像解析結果**")
                st.write("")
                extracted_address = st.session_state.get('extracted_address', '不明')
                st.write(f"**抽出された住所**: {extracted_address}")
                raw_texts = st.session_state.get('raw_texts', [])
                if raw_texts:
                    st.write(f"**抽出されたテキスト**: {len(raw_texts)}件")
            
            # 1. ジオコーディング
            progress_bar.progress(20)
            with st.chat_message("assistant"):
                st.write("")
                st.write("📍 **ジオコーディング開始**")
            geocoder = create_geocoder(
                google_api_key=google_maps_api_key,
                geocoding_api_key=config.get('geocoding_api_key', '')
            )
            
            with time_block("ジオコーディング"):
                geocode_result = geocoder.geocode_address(address)
            if not geocode_result.get('success'):
                with st.chat_message("assistant"):
                    st.error(f"❌ ジオコーディングに失敗しました: {geocode_result.get('error', '不明なエラー')}")
                st.session_state['chat_step'] = 'result'
                return
            
            lat = geocode_result['latitude']
            lng = geocode_result['longitude']
            
            progress_bar.progress(40)
            with st.chat_message("assistant"):
                st.success("✅ ジオコーディング完了")
                st.write("")
                st.write(f"**緯度**: {lat}")
                st.write(f"**経度**: {lng}")
            
            # 2. 用途地域判定
            progress_bar.progress(60)
            with st.chat_message("assistant"):
                st.write("")
                st.write("🏘️ **用途地域判定開始**")
            zoning_checker = create_zoning_checker()
            
            # 都道府県を抽出
            from modules.utils import extract_prefecture_from_address
            prefecture = extract_prefecture_from_address(address)
            
            with time_block("用途地域判定"):
                zoning_result = zoning_checker.check_zoning_by_coordinates(
                    latitude=lat,
                    longitude=lng,
                    prefecture=prefecture
                )
            
            progress_bar.progress(80)
            if zoning_result.get('success'):
                zoning_type = zoning_result.get('zoning_type', '不明')
                zoning_code = zoning_result.get('zoning_code', '')
                
                with st.chat_message("assistant"):
                    st.success("✅ 用途地域判定完了")
                    st.write("")
                    st.write(f"**用途地域**: {zoning_type}")
                    if zoning_code:
                        st.write(f"**用途地域コード**: {zoning_code}")
            else:
                zoning_type = '不明'
                with st.chat_message("assistant"):
                    error_msg = zoning_result.get('error', '用途地域を判定できませんでした')
                    st.warning(f"⚠️ {error_msg}")
                    # デバッグ情報を表示（開発時のみ）
                    if 'file_checked' in zoning_result and len(zoning_result['file_checked']) > 0:
                        st.caption(f"チェックしたファイル数: {len(zoning_result['file_checked'])}")
            
            st.session_state['zoning_type'] = zoning_type
            st.session_state['latitude'] = lat
            st.session_state['longitude'] = lng
            
            # 3. 法令判定
            progress_bar.progress(90)
            with st.chat_message("assistant"):
                st.write("")
                st.write("⚖️ **法令判定開始**")
            if gemini_api_key:
                law_checker = create_law_checker(gemini_api_key=gemini_api_key)
                
                if law_checker.gemini_available:
                    from modules.law_result_formatter import (
                        format_property_info, format_permission_results,
                        format_fire_law_results, format_building_standards_results,
                        format_local_restrictions
                    )
                    
                    # 1. 物件情報の抽出
                    raw_texts = st.session_state.get('raw_texts', [])
                    if raw_texts:
                        extracted_text = '\n'.join(raw_texts)
                        with time_block("物件情報抽出"):
                            extract_result = law_checker.extract_property_info(extracted_text)
                        property_info = extract_result.get('property_info', {})
                        property_info['所在地'] = address
                        property_info['用途地域'] = zoning_type
                    else:
                        property_info = {'所在地': address, '用途地域': zoning_type}
                    
                    # 物件情報を表示
                    with st.chat_message("assistant"):
                        st.write("")
                        st.markdown("### 📊 判定結果")
                        st.markdown(format_property_info(property_info))
                    
                    # 2. 民泊の許可判定（順次実行・表示）
                    progress_bar.progress(92)
                    # 進行中メッセージを一時的に表示
                    status_placeholder_1 = st.empty()
                    with status_placeholder_1.container():
                        with st.chat_message("assistant"):
                            st.write("🔍 **民泊の許可判定を実行中...**")
                    
                    with time_block("民泊許可判定"):
                        minpaku_result = law_checker.check_minpaku_permission(zoning_type, address)
                        ryokan_result = law_checker.check_ryokan_permission(zoning_type, address)
                        tokku_result = law_checker.check_tokku_minpaku_permission(zoning_type, address)
                    
                    # 進行中メッセージを削除して結果を表示
                    status_placeholder_1.empty()
                    with st.chat_message("assistant"):
                        st.markdown(format_permission_results(minpaku_result, ryokan_result, tokku_result))
                    
                    # 3. 消防法上のポイント（順次実行・表示）
                    progress_bar.progress(94)
                    status_placeholder_2 = st.empty()
                    with status_placeholder_2.container():
                        with st.chat_message("assistant"):
                            st.write("🔥 **消防法上のポイントを判定中...**")
                    
                    with time_block("消防法判定"):
                        fire_result = law_checker.check_fire_law_requirements(
                            property_info.get('建物用途', '不明'),
                            property_info.get('構造', '不明'),
                            property_info.get('階数', '不明'),
                            property_info.get('延べ床面積', '不明')
                        )
                    
                    # 進行中メッセージを削除して結果を表示
                    status_placeholder_2.empty()
                    with st.chat_message("assistant"):
                        st.markdown(format_fire_law_results(fire_result))
                    
                    # 4. 建築基準法上のポイント（順次実行・表示）
                    progress_bar.progress(96)
                    status_placeholder_3 = st.empty()
                    with status_placeholder_3.container():
                        with st.chat_message("assistant"):
                            st.write("🏗️ **建築基準法上のポイントを判定中...**")
                    
                    with time_block("建築基準法判定"):
                        building_result = law_checker.check_building_standards_requirements(
                            property_info.get('建物用途', '不明'),
                            property_info.get('構造', '不明'),
                            property_info.get('階数', '不明'),
                            property_info.get('延べ床面積', '不明')
                        )
                    
                    # 進行中メッセージを削除して結果を表示
                    status_placeholder_3.empty()
                    with st.chat_message("assistant"):
                        st.markdown(format_building_standards_results(building_result))
                    
                    # 5. その他の留意点（順次実行・表示）
                    progress_bar.progress(98)
                    status_placeholder_4 = st.empty()
                    with status_placeholder_4.container():
                        with st.chat_message("assistant"):
                            st.write("📋 **その他の留意点を確認中...**")
                    
                    with time_block("ローカル制限確認"):
                        local_result = law_checker.check_local_restrictions(address)
                    
                    # 進行中メッセージを削除して結果を表示
                    status_placeholder_4.empty()
                    with st.chat_message("assistant"):
                        st.markdown(format_local_restrictions(local_result))
                    
                    # 6. 次に取るべきアクション（最後に表示）
                    progress_bar.progress(100)
                    status_placeholder_5 = st.empty()
                    with status_placeholder_5.container():
                        with st.chat_message("assistant"):
                            st.write("💡 **次に取るべきアクションを生成中...**")
                    
                    suggestions = suggest_next_action(
                        zoning_type, minpaku_result, ryokan_result, tokku_result,
                        fire_result, building_result, local_result,
                        law_checker=law_checker
                    )
                    
                    # 進行中メッセージを削除して結果を表示
                    status_placeholder_5.empty()
                    with st.chat_message("assistant"):
                        st.write("")
                        st.markdown("### 💡 次に取るべきアクション")
                        # 改行が正しく表示されるように、各行を個別に表示
                        for line in suggestions.split('\n'):
                            if line.strip():
                                st.markdown(line)
                            else:
                                st.write("")  # 空行
                    
                    # 法令判定結果をセッション状態に保存（チャット対話で使用）
                    st.session_state['law_check_results'] = {
                        'property_info': property_info,
                        'minpaku_result': minpaku_result,
                        'ryokan_result': ryokan_result,
                        'tokku_result': tokku_result,
                        'fire_result': fire_result,
                        'building_result': building_result,
                        'local_result': local_result,
                        'zoning_type': zoning_type,
                        'address': address,
                        'coordinates': {'lat': lat, 'lng': lng},
                        'suggestions': suggestions,
                        'formatted_result': format_law_check_results(
                            property_info, minpaku_result, ryokan_result, tokku_result,
                            fire_result, building_result, local_result
                        )
                    }
                    st.session_state['law_checker_instance'] = law_checker  # Gemini APIインスタンスを保存
                    
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': '✅ すべての処理が完了しました！\n\n法令判定結果について何かご質問がございましたら、お気軽にお聞きください。',
                        'data': {
                            '住所位置': f'{lat}, {lng}',
                            '用途地域': zoning_type,
                            '民泊新法': minpaku_result.get('permission', '判定不可') if minpaku_result.get('success') else 'エラー',
                            '次に取るべきアクション': suggestions
                        }
                    })
                else:
                    with st.chat_message("assistant"):
                        st.warning("⚠️ Gemini APIが利用できないため、法令判定をスキップしました")
            else:
                progress_bar.progress(100)
                with st.chat_message("assistant"):
                    st.warning("⚠️ Gemini APIキーが設定されていないため、法令判定をスキップしました")
            
            st.session_state['chat_step'] = 'result'
            progress_bar.empty()
            
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"❌ 処理中にエラーが発生しました: {str(e)}")
            st.session_state['chat_step'] = 'result'
    
    # ステップ4: 結果表示とチャット対話
    if st.session_state['chat_step'] == 'result':
        # チャット入力（法令判定結果について質問）
        if 'law_check_results' in st.session_state and 'law_checker_instance' in st.session_state:
            law_checker = st.session_state.get('law_checker_instance')
            
            if law_checker and law_checker.gemini_available:
                # チャット入力フィールド
                user_question = st.chat_input("法令判定結果について質問してください...")
                
                if user_question:
                    # ユーザーの質問をチャット履歴に追加
                    st.session_state['chat_history'].append({
                        'role': 'user',
                        'content': user_question
                    })
                    
                    # 法令判定結果をコンテキストとして取得
                    law_results = st.session_state['law_check_results']
                    
                    # Gemini APIを使って回答を生成
                    context_prompt = f"""あなたは民泊開業の適法性について専門的なアドバイスを提供するAIアシスタントです。

以下の法令判定結果を基に、ユーザーの質問に丁寧に答えてください。

【物件情報】
{law_results['formatted_result']}

【次に取るべきアクション】
{law_results['suggestions']}

【その他の情報】
- 所在地: {law_results['address']}
- 用途地域: {law_results['zoning_type']}
- 緯度経度: {law_results['coordinates']['lat']}, {law_results['coordinates']['lng']}

ユーザーの質問に対して、上記の法令判定結果を参照しながら、具体的で実用的な回答を提供してください。
回答は簡潔で分かりやすく、必要に応じて法令の根拠や具体的な手続きについても説明してください。"""

                    user_prompt = f"{context_prompt}\n\n【ユーザーの質問】\n{user_question}\n\n【回答】"
                    
                    # 回答を生成
                    with st.chat_message("assistant"):
                        with st.spinner("回答を生成中..."):
                            response = law_checker._call_gemini(user_prompt)
                            
                            # 回答を表示
                            if response and response != "Gemini APIが利用できません" and not response.startswith("エラー"):
                                st.markdown(response)
                                
                                # チャット履歴に追加
                                st.session_state['chat_history'].append({
                                    'role': 'assistant',
                                    'content': response
                                })
                            else:
                                st.error("❌ 回答の生成に失敗しました。もう一度お試しください。")
                    
                    st.rerun()
        
        # リセットボタン
        st.write("")
        if st.button("🔄 新しい画像で再開", type="primary"):
            st.session_state['chat_history'] = []
            st.session_state['chat_step'] = 'upload'
            st.session_state['extracted_address'] = None
            st.session_state['selected_address'] = None
            st.session_state['raw_texts'] = None
            st.session_state.pop('law_check_results', None)
            st.session_state.pop('law_checker_instance', None)
            st.rerun()


def simulation_tab():
    """投資シミュレーションタブ"""
    st.header("💰 投資回収シミュレーション")
    
    # 投資シミュレーターを作成
    simulator = create_investment_simulator()
    
    # 初期費用推定器を関数レベルで初期化（初期費用・運用費用の両方で使用）
    initial_cost_estimator = None
    
    # 住所と面積を取得（価格推定用）
    address = st.session_state.get('selected_address') or st.session_state.get('extracted_address', '')
    law_check_results = st.session_state.get('law_check_results')
    if law_check_results is None:
        law_check_results = {}
    property_info = law_check_results.get('property_info', {})
    if property_info is None:
        property_info = {}
    area_str = property_info.get('延べ床面積', '不明')
    
    # 面積を数値に変換
    area = None
    if area_str and area_str != '不明':
        try:
            # 文字列から数値を抽出
            numbers = re.findall(r'\d+\.?\d*', str(area_str))
            if numbers:
                area = float(numbers[0])
        except:
            pass
    
    # Gemini APIキーを取得
    gemini_api_key = st.session_state.get('gemini_api_key', '')
    
    # デフォルトの単価を設定
    default_daily_rate = simulator.default_rates['daily_rate']
    
    # 条件が揃っている場合は価格推定を実行（パラメータ設定の前に表示）
    price_estimation_info = None
    if address and gemini_api_key:
        # キャッシュキーを作成
        cache_key = f"airbnb_price_{address}_{area}"
        
        # キャッシュを確認
        if cache_key not in st.session_state:
            try:
                # Airbnb価格推定器を作成
                price_estimator = create_airbnb_price_estimator(gemini_api_key=gemini_api_key)
                
                if price_estimator.gemini_available:
                    # 価格推定を実行
                    with time_block("Airbnb価格推定"):
                        price_estimation_info = price_estimator.estimate_price(address, area)
                    
                    # 結果をキャッシュ
                    st.session_state[cache_key] = price_estimation_info
                else:
                    st.session_state[cache_key] = None
            except Exception as e:
                log_error(f"Airbnb価格推定エラー: {str(e)}")
                st.session_state[cache_key] = None
        else:
            # キャッシュから取得
            price_estimation_info = st.session_state[cache_key]
    
    # 推定された価格をデフォルト値として使用
    if price_estimation_info and price_estimation_info.get('success'):
        estimated_price = price_estimation_info.get('average_price_median', 0)
        if estimated_price and estimated_price > 0:
            default_daily_rate = int(estimated_price)
    
    # 価格推定結果の表示（パラメータ設定の前に表示）
    if price_estimation_info:
        search_level = price_estimation_info.get('search_level')
        search_address = price_estimation_info.get('search_address')
        level_info = ""
        if search_level and search_address:
            level_info = f"【検索レベル: {search_level}（{search_address}）】"
        
        # 青色の情報ボックスに価格情報を表示
        price_info_text = f"💡 Geminiで推定した価格: {price_estimation_info.get('average_price_median_str', '¥0')} (範囲: {price_estimation_info.get('price_range', '¥0〜¥0')}, {price_estimation_info.get('property_count_str', '0件')}) {level_info}"
        
        # 価格情報を表示
        st.info(price_info_text)
        
        # 抽出したリスティング情報があれば、推定根拠の上に表示
        listing_data = price_estimation_info.get('listing_data', [])
        if listing_data and len(listing_data) > 0:
            df_listings = pd.DataFrame(listing_data)
            # 列名を「タイトル」「概要」「価格」に統一
            if '概要説明' in df_listings.columns:
                df_listings = df_listings.rename(columns={'概要説明': '概要'})
            
            # リスティング情報の表を表示（青色の背景で）
            table_html = df_listings.to_html(index=False, escape=False, classes='listing-table')
            st.markdown(
                f"""
                <div style="background-color: #D1ECF1; padding: 1rem; border-radius: 0.5rem; margin-top: 0.5rem;">
                    <p style="margin-bottom: 0.5rem; font-weight: bold;">📋 抽出したリスティング情報</p>
                    {table_html}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # 推定根拠を表示（リスティング情報の下）
        estimation_basis = price_estimation_info.get('estimation_basis', '')
        if estimation_basis:
            st.info(f"📊 推定根拠: {estimation_basis}")
    
    # 価格推定を試みたが失敗した場合、エラー情報を表示（デバッグ用）
    elif address and gemini_api_key:
        # キャッシュキーを確認
        cache_key = f"airbnb_price_{address}_{area}"
        if cache_key in st.session_state and st.session_state[cache_key] is None:
            st.warning("⚠️ Airbnb価格推定に失敗しました。デフォルト値（¥15,000）を使用します。")
    
    # 初期費用のデフォルト値を計算（パラメータ設定の前に実行）
    # OCRテキストを取得
    raw_texts = st.session_state.get('raw_texts', [])
    extracted_text = '\n'.join(raw_texts) if raw_texts else ''
    
    # キャッシュキーを作成
    cache_key_initial_costs = f"initial_costs_{address}_{area}"
    
    # キャッシュから取得または計算
    if cache_key_initial_costs not in st.session_state:
        
        # エラー情報を保存するための変数（ログ表示領域に表示するため）
        initial_costs_errors = []
        
        default_initial_costs = {
            'deposit': 0,           # 敷金
            'key_money': 0,         # 礼金
            'brokerage_fee': 0,     # 仲介手数料
            'guarantee_company': 0, # 保証会社
            'fire_insurance': 0,    # 火災保険
            'fire_equipment': 0,    # 消防設備
            'furniture': 0,         # 家具・家電購入費用
            'renovation': 0,        # リノベーション費用
            'license_fee': 0        # 許可・届出費用
        }
        
        # OCRテキストから初期費用項目を抽出
        if extracted_text and gemini_api_key:
            try:
                if initial_cost_estimator is None:
                    initial_cost_estimator = create_initial_cost_estimator(gemini_api_key=gemini_api_key)
                ocr_costs = initial_cost_estimator.extract_initial_costs_from_ocr(extracted_text)
                default_initial_costs.update(ocr_costs)
                # ログは後で表示領域に出力
            except Exception as e:
                log_error(f"初期費用抽出エラー: {str(e)}")
        
        # 宿泊人数を計算（面積から）
        occupancy = 2  # デフォルト
        if area:
            occupancy = max(1, min(10, round(area / 12)))
        
        # 間取り情報を取得（OCRテキストから抽出を試みる）
        layout = property_info.get('間取り', '')
        if not layout:
            # 間取り情報が取得できない場合は階数情報を使用
            layout = property_info.get('階数', '')
        
        # 消防設備費用と家具・家電購入費用を推定（内訳も取得）
        fire_equipment_result = {'cost': 0, 'breakdown': ''}
        furniture_result = {'cost': 0, 'breakdown': ''}
        
        # 初期費用推定器がまだ作成されていない場合は作成
        if gemini_api_key and initial_cost_estimator is None:
            try:
                initial_cost_estimator = create_initial_cost_estimator(gemini_api_key=gemini_api_key)
            except Exception as e:
                error_msg = f"初期費用推定器作成エラー: {str(e)}"
                initial_costs_errors.append(error_msg)
                print(f"[ERROR] {error_msg}", file=sys.stderr)
        
        if gemini_api_key and initial_cost_estimator:
            try:
                fire_result = law_check_results.get('fire_result', {})
                if fire_result:
                    with time_block("消防設備費用推定"):
                        fire_equipment_result = initial_cost_estimator.estimate_fire_equipment_cost(fire_result)
                    if fire_equipment_result.get('cost', 0) > 0:
                        default_initial_costs['fire_equipment'] = fire_equipment_result['cost']
            except Exception as e:
                error_msg = f"消防設備費用推定エラー: {str(e)}"
                initial_costs_errors.append(error_msg)
                print(f"[ERROR] {error_msg}", file=sys.stderr)
            
            try:
                with time_block("家具・家電購入費用推定"):
                    furniture_result = initial_cost_estimator.estimate_furniture_cost(
                        area=area,
                        occupancy=occupancy,
                        layout=layout
                    )
                if furniture_result.get('cost', 0) > 0:
                    default_initial_costs['furniture'] = furniture_result['cost']
            except Exception as e:
                error_msg = f"家具・家電購入費用推定エラー: {str(e)}"
                initial_costs_errors.append(error_msg)
                print(f"[ERROR] {error_msg}", file=sys.stderr)
        
        # キャッシュに保存（ログ出力用の情報も保存）
        st.session_state[cache_key_initial_costs] = default_initial_costs
        st.session_state[f"{cache_key_initial_costs}_logs"] = {
            'ocr_costs': ocr_costs if extracted_text and gemini_api_key and initial_cost_estimator else None,
            'fire_equipment_result': fire_equipment_result,
            'furniture_result': furniture_result,
            'errors': initial_costs_errors  # エラー情報も保存
        }
    else:
        # キャッシュから取得
        default_initial_costs = st.session_state[cache_key_initial_costs]
    
    # ログ表示領域に初期費用推定結果を出力（パラメータ設定の前に表示）
    log_key = f"{cache_key_initial_costs}_logs"
    if log_key in st.session_state:
        log_data = st.session_state[log_key]
        
        # エラー情報をログ表示領域に表示（最初に表示）
        errors = log_data.get('errors', [])
        if errors:
            for error_msg in errors:
                log_error(error_msg)
        
        # OCRから抽出した初期費用をログ表示
        if log_data.get('ocr_costs'):
            log_info(f"OCRから初期費用を抽出: {log_data['ocr_costs']}")
        
        # 推定結果をログ表示領域に出力（内訳も含む）
        fire_equipment_result = log_data.get('fire_equipment_result', {'cost': 0, 'breakdown': ''})
        furniture_result = log_data.get('furniture_result', {'cost': 0, 'breakdown': ''})
        
        if fire_equipment_result.get('cost', 0) > 0 or furniture_result.get('cost', 0) > 0:
            log_info("📊 初期費用推定結果:")
            if fire_equipment_result.get('cost', 0) > 0:
                log_info(f"  消防設備費用: ¥{fire_equipment_result['cost']:,}")
                if fire_equipment_result.get('breakdown'):
                    log_info(f"    └ 内訳: {fire_equipment_result['breakdown']}")
            if furniture_result.get('cost', 0) > 0:
                log_info(f"  家具・家電購入費用: ¥{furniture_result['cost']:,}")
                if furniture_result.get('breakdown'):
                    log_info(f"    └ 内訳: {furniture_result['breakdown']}")
    
    # 運用費用のデフォルト値を計算（パラメータ設定の前に実行、ログ表示の前に計算）
    cache_key_operating_costs = f"operating_costs_{address}_{area}"
    
    # エラー情報を保存するための変数（ログ表示領域に表示するため）
    operating_costs_errors = []
    
    # 宿泊人数を計算（面積から）- 運用費用計算でも使用
    occupancy = 2  # デフォルト
    if area:
        occupancy = max(1, min(10, round(area / 12)))
    
    # 間取り情報を取得（OCRテキストから抽出を試みる）
    layout = property_info.get('間取り', '')
    if not layout:
        # 間取り情報が取得できない場合は階数情報を使用
        layout = property_info.get('階数', '')
    
    # キャッシュから取得または計算
    if cache_key_operating_costs not in st.session_state:
        default_operating_costs = {
            'rent': 0,              # 家賃
            'utilities': 0,         # 水道光熱費
            'communication': 5000,  # 通信費（デフォルト¥5,000/月）
            'insurance': 5000,      # 保険費（デフォルト¥5,000/月）
            'cleaning': 0,          # 清掃費
            'supplies': 0           # 消耗品
        }
        
        # 変数を初期化（ログ出力用）
        rent_data = None
        utilities_result = {'cost': 0, 'breakdown': ''}
        insurance_result = {'cost': 5000, 'breakdown': 'デフォルト値'}
        cleaning_result = {'cost': 0, 'breakdown': ''}
        supplies_result = {'cost': 0, 'breakdown': ''}
        
        # 初期費用推定器を初期化（既存のものを再利用、なければ新規作成）
        try:
            if initial_cost_estimator is None and gemini_api_key:
                initial_cost_estimator = create_initial_cost_estimator(gemini_api_key=gemini_api_key)
        except Exception as e:
            error_msg = f"初期費用推定器作成エラー: {str(e)}"
            operating_costs_errors.append(error_msg)
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            initial_cost_estimator = None
        
        # OCRテキストから家賃と管理費を抽出
        if extracted_text and gemini_api_key and initial_cost_estimator:
            try:
                rent_data = initial_cost_estimator.extract_rent_from_ocr(extracted_text)
                # 家賃と管理費を合計して家賃として扱う
                default_operating_costs['rent'] = rent_data.get('rent', 0) + rent_data.get('management_fee', 0)
            except Exception as e:
                error_msg = f"家賃抽出エラー: {str(e)}"
                operating_costs_errors.append(error_msg)
                print(f"[ERROR] {error_msg}", file=sys.stderr)
        
        # 水道光熱費、保険費、清掃費、消耗品を推定
        if gemini_api_key and initial_cost_estimator:
            try:
                with time_block("運用費用推定"):
                    # 水道光熱費を推定
                    utilities_result = initial_cost_estimator.estimate_utilities_cost(
                        area=area,
                        occupancy=occupancy,
                        layout=layout
                    )
                    if utilities_result.get('cost', 0) > 0:
                        default_operating_costs['utilities'] = utilities_result['cost']
                    
                    # 保険費を推定
                    structure = property_info.get('構造', '')
                    insurance_result = initial_cost_estimator.estimate_insurance_cost(
                        area=area,
                        occupancy=occupancy,
                        layout=layout,
                        address=address,
                        structure=structure
                    )
                    if insurance_result.get('cost', 0) > 0:
                        default_operating_costs['insurance'] = insurance_result['cost']
                    
                    # 清掃費を推定
                    cleaning_result = initial_cost_estimator.estimate_cleaning_cost(
                        area=area,
                        occupancy=occupancy,
                        layout=layout,
                        address=address
                    )
                    if cleaning_result.get('cost', 0) > 0:
                        default_operating_costs['cleaning'] = cleaning_result['cost']
                    
                    # 消耗品を推定
                    supplies_result = initial_cost_estimator.estimate_supplies_cost(
                        area=area,
                        occupancy=occupancy,
                        layout=layout
                    )
                    if supplies_result.get('cost', 0) > 0:
                        default_operating_costs['supplies'] = supplies_result['cost']
            except Exception as e:
                error_msg = f"運用費用推定エラー: {str(e)}"
                operating_costs_errors.append(error_msg)
                print(f"[ERROR] {error_msg}", file=sys.stderr)
        
        # キャッシュに保存（ログ出力用の情報も保存）
        st.session_state[cache_key_operating_costs] = default_operating_costs
        st.session_state[f"{cache_key_operating_costs}_logs"] = {
            'rent_data': rent_data,
            'utilities_result': utilities_result,
            'insurance_result': insurance_result,
            'cleaning_result': cleaning_result,
            'supplies_result': supplies_result,
            'errors': operating_costs_errors  # エラー情報も保存
        }
    else:
        # キャッシュから取得
        default_operating_costs = st.session_state.get(cache_key_operating_costs, {
            'rent': 0,
            'utilities': 0,
            'communication': 5000,
            'insurance': 5000,
            'cleaning': 0,
            'supplies': 0
        })
    
    # 運用費用推定結果をログ表示領域に出力（パラメータ設定の前に表示）
    log_key_operating = f"{cache_key_operating_costs}_logs"
    if log_key_operating in st.session_state:
        log_data_operating = st.session_state[log_key_operating]
        
        # エラー情報をログ表示領域に表示（最初に表示）
        errors = log_data_operating.get('errors', [])
        if errors:
            for error_msg in errors:
                log_error(error_msg)
        
        # 家賃抽出結果をログ表示
        if log_data_operating.get('rent_data'):
            rent_data = log_data_operating['rent_data']
            if rent_data.get('rent', 0) > 0 or rent_data.get('management_fee', 0) > 0:
                log_info(f"OCRから家賃を抽出: 家賃=¥{rent_data.get('rent', 0):,}, 管理費=¥{rent_data.get('management_fee', 0):,}, 合計=¥{rent_data.get('rent', 0) + rent_data.get('management_fee', 0):,}")
        
        # 推定結果をログ表示領域に出力（内訳も含む）
        utilities_result = log_data_operating.get('utilities_result', {'cost': 0, 'breakdown': ''})
        insurance_result = log_data_operating.get('insurance_result', {'cost': 5000, 'breakdown': 'デフォルト値'})
        cleaning_result = log_data_operating.get('cleaning_result', {'cost': 0, 'breakdown': ''})
        supplies_result = log_data_operating.get('supplies_result', {'cost': 0, 'breakdown': ''})
        
        has_operating_logs = (
            utilities_result.get('cost', 0) > 0 or
            (insurance_result.get('cost', 0) > 0 and insurance_result.get('cost', 0) != 5000) or
            cleaning_result.get('cost', 0) > 0 or
            supplies_result.get('cost', 0) > 0
        )
        
        if has_operating_logs:
            log_info("📊 運用費用推定結果:")
            if utilities_result.get('cost', 0) > 0:
                log_info(f"  水道光熱費: ¥{utilities_result['cost']:,}")
                if utilities_result.get('breakdown'):
                    log_info(f"    └ 内訳: {utilities_result['breakdown']}")
            if insurance_result.get('cost', 0) > 0:
                log_info(f"  保険費: ¥{insurance_result['cost']:,}")
                if insurance_result.get('breakdown') and insurance_result.get('breakdown') != 'デフォルト値':
                    log_info(f"    └ 内訳: {insurance_result['breakdown']}")
            if cleaning_result.get('cost', 0) > 0:
                log_info(f"  清掃費: ¥{cleaning_result['cost']:,}")
                if cleaning_result.get('breakdown'):
                    log_info(f"    └ 内訳: {cleaning_result['breakdown']}")
            if supplies_result.get('cost', 0) > 0:
                log_info(f"  消耗品: ¥{supplies_result['cost']:,}")
                if supplies_result.get('breakdown'):
                    log_info(f"    └ 内訳: {supplies_result['breakdown']}")
    
    # パラメータ設定
    st.subheader("パラメータ設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**初期費用**")
        # 再計算ボタン（オプション）
        if gemini_api_key and (extracted_text or law_check_results.get('fire_result')):
            if st.button("🔄 初期費用を再計算", help="OCRテキストや法令判定結果から初期費用を再推定します"):
                # キャッシュをクリア
                if cache_key_initial_costs in st.session_state:
                    del st.session_state[cache_key_initial_costs]
                st.rerun()
        
        deposit = st.number_input("敷金（円）", value=default_initial_costs.get('deposit', 0), step=10000, min_value=0, format="%d")
        key_money = st.number_input("礼金（円）", value=default_initial_costs.get('key_money', 0), step=10000, min_value=0, format="%d")
        brokerage_fee = st.number_input("仲介手数料（円）", value=default_initial_costs.get('brokerage_fee', 0), step=10000, min_value=0, format="%d")
        guarantee_company = st.number_input("保証会社（円）", value=default_initial_costs.get('guarantee_company', 0), step=10000, min_value=0, format="%d")
        fire_insurance = st.number_input("火災保険", value=default_initial_costs.get('fire_insurance', 0), step=10000)
        fire_equipment = st.number_input("消防設備", value=default_initial_costs.get('fire_equipment', 0), step=10000)
        furniture = st.number_input("家具・家電購入費用", value=default_initial_costs.get('furniture', 0), step=100000)
        renovation = st.number_input("リノベーション費用", value=default_initial_costs.get('renovation', 0), step=100000)
        license_fee = st.number_input("許可・届出費用", value=default_initial_costs.get('license_fee', 0), step=10000)
    
    with col2:
        st.write("**運用費用（月額）**")
        
        # 運用費用のデフォルト値は既に計算済み（上記のブロックで計算）
        # ここではキャッシュから取得した値を使用（既に default_operating_costs 変数に格納されている）
        
        # 再計算ボタン（オプション）
        if gemini_api_key and (extracted_text or area):
            if st.button("🔄 運用費用を再計算", help="OCRテキストや物件情報から運用費用を再推定します", key="recalc_operating"):
                # キャッシュをクリア
                if cache_key_operating_costs in st.session_state:
                    del st.session_state[cache_key_operating_costs]
                if f"{cache_key_operating_costs}_logs" in st.session_state:
                    del st.session_state[f"{cache_key_operating_costs}_logs"]
                st.rerun()
        
        rent = st.number_input("家賃", value=default_operating_costs.get('rent', 0), step=10000, help="家賃＋管理費")
        utilities = st.number_input("水道光熱費", value=default_operating_costs.get('utilities', 0), step=5000)
        communication = st.number_input("通信費", value=default_operating_costs.get('communication', 5000), step=1000)
        insurance = st.number_input("保険費", value=default_operating_costs.get('insurance', 5000), step=1000)
        cleaning = st.number_input("清掃費", value=default_operating_costs.get('cleaning', 0), step=5000)
        supplies = st.number_input("消耗品", value=default_operating_costs.get('supplies', 0), step=5000)
    
    # 収益パラメータ
    st.subheader("収益パラメータ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        daily_rate = st.number_input("1泊あたりの単価", value=int(default_daily_rate), step=1000)
        commission_rate = st.slider("手数料率（％）", 0.0, 0.3, 0.15, 0.01, help="Airbnbなどのプラットフォーム手数料率")
        tax_rate = st.slider("税率", 0.0, 0.5, 0.1, 0.01)
    
    with col2:
        min_occupancy = st.slider("最小稼働率", 0.1, 0.9, 0.3, 0.1)
        max_occupancy = st.slider("最大稼働率", 0.1, 0.9, 0.9, 0.1)
    
    # 稼働率のリストを生成
    occupancy_rates = [round(x, 1) for x in [min_occupancy + i * 0.1 for i in range(int((max_occupancy - min_occupancy) * 10) + 1)]]
    
    # シミュレーション実行
    if st.button("シミュレーション実行", type="primary"):
        with st.spinner("シミュレーション実行中..."):
            try:
                # パラメータを設定
                initial_costs = {
                    'deposit': deposit,
                    'key_money': key_money,
                    'brokerage_fee': brokerage_fee,
                    'guarantee_company': guarantee_company,
                    'fire_insurance': fire_insurance,
                    'fire_equipment': fire_equipment,
                    'furniture': furniture,
                    'renovation': renovation,
                    'license_fee': license_fee
                }
                
                operating_costs = {
                    'rent': rent,
                    'utilities': utilities,
                    'communication': communication,
                    'insurance': insurance,
                    'cleaning': cleaning,
                    'supplies': supplies,
                    'commission_rate': commission_rate
                }
                
                # シミュレーション実行
                with time_block("シミュレーション計算"):
                    result = simulator.run_simulation(
                        initial_costs=initial_costs,
                        operating_costs=operating_costs,
                        daily_rate=daily_rate,
                        occupancy_rates=occupancy_rates,
                        tax_rate=tax_rate
                    )
                
                if result['success']:
                    st.success("シミュレーションが完了しました！")
                    
                    # 結果を表示
                    st.subheader("シミュレーション結果")
                    
                    # 初期投資額
                    st.write("**初期投資額**")
                    initial_investment = result['initial_investment']['total']
                    st.metric("総初期投資額", f"¥{initial_investment:,}")
                    
                    # 年間運用費用
                    st.write("**年間運用費用**")
                    annual_costs = result['annual_operating_costs']['annual_costs']
                    st.metric("年間運用費用", f"¥{annual_costs:,}")
                    
                    # 損益分岐点
                    st.write("**損益分岐点**")
                    breakeven_rate = result['breakeven_rate']
                    st.metric("損益分岐点稼働率", f"{breakeven_rate:.1%}")
                    
                    # 結果テーブル
                    st.subheader("稼働率別シミュレーション結果")
                    df = simulator.create_simulation_dataframe(result['simulation_results'])
                    st.dataframe(df, use_container_width=True)
                    
                    # グラフ表示
                    st.subheader("収益性グラフ")
                    
                    # データを準備
                    simulation_data = result['simulation_results']
                    df_plot = pd.DataFrame(simulation_data)
                    
                    # 収益性グラフ
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df_plot['occupancy_rate'],
                        y=df_plot['net_profit'],
                        mode='lines+markers',
                        name='税引後利益',
                        line=dict(color='green', width=3)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_plot['occupancy_rate'],
                        y=df_plot['annual_revenue'],
                        mode='lines+markers',
                        name='年間収益',
                        line=dict(color='blue', width=2)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df_plot['occupancy_rate'],
                        y=[annual_costs] * len(df_plot),
                        mode='lines',
                        name='年間費用',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title="稼働率別収益性",
                        xaxis_title="稼働率",
                        yaxis_title="金額 (円)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 投資回収年数グラフ
                    st.subheader("投資回収年数")
                    
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Scatter(
                        x=df_plot['occupancy_rate'],
                        y=df_plot['payback_years'],
                        mode='lines+markers',
                        name='投資回収年数',
                        line=dict(color='purple', width=3)
                    ))
                    
                    fig2.update_layout(
                        title="稼働率別投資回収年数",
                        xaxis_title="稼働率",
                        yaxis_title="年数",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # 推奨事項
                    st.subheader("推奨事項")
                    recommendations = simulator.get_recommendations(result['simulation_results'])
                    for rec in recommendations:
                        st.write(f"• {rec}")
                
                else:
                    st.error(f"シミュレーションに失敗しました: {result.get('error', '不明なエラー')}")
                    
            except Exception as e:
                st.error(f"処理中にエラーが発生しました: {str(e)}")


def _render_chat_history_sidebar():
    """サイドバーにチャット履歴を表示"""
    st.header("💬 チャット履歴")
    
    # チャット履歴の初期化
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    # チャットルーム管理の初期化
    if 'chat_rooms' not in st.session_state:
        st.session_state['chat_rooms'] = []
    
    if 'current_room_id' not in st.session_state:
        import uuid
        st.session_state['current_room_id'] = str(uuid.uuid4())
        st.session_state['chat_rooms'].append({
            'id': st.session_state['current_room_id'],
            'title': '新しいチャット',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # チャット履歴を表示
    chat_history = st.session_state.get('chat_history', [])
    if chat_history:
        st.markdown("**現在のチャット**")
        # 最初と最後の数件を表示（スクロール可能）
        with st.container():
            # 簡潔に表示（タイトルや概要のみ）
            if len(chat_history) > 0:
                first_msg = chat_history[0].get('content', '')[:50]
                st.caption(f"📝 {first_msg}...")
        
        st.markdown("---")
    
    # 新しいチャット開始ボタン
    if st.button("🔄 新しいチャット", use_container_width=True):
        _create_new_chat_room()
        st.rerun()
    
    # チャットルーム一覧
    if st.session_state.get('chat_rooms'):
        st.markdown("**過去のチャット**")
        for room in st.session_state['chat_rooms']:
            room_title = room.get('title', 'チャット')
            room_time = room.get('created_at', '')
            if st.button(f"💬 {room_title}", key=f"room_{room['id']}", use_container_width=True):
                _load_chat_room(room['id'])
                st.rerun()


def _create_new_chat_room():
    """新しいチャットルームを作成"""
    import uuid
    new_room_id = str(uuid.uuid4())
    st.session_state['current_room_id'] = new_room_id
    st.session_state['chat_history'] = []
    st.session_state['chat_step'] = 'upload'  # チャットステップをリセット
    st.session_state['chat_rooms'].append({
        'id': new_room_id,
        'title': f'チャット {len(st.session_state.get("chat_rooms", [])) + 1}',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


def _load_chat_room(room_id: str):
    """指定されたチャットルームを読み込む"""
    st.session_state['current_room_id'] = room_id
    # チャット履歴は既にセッションステートに保持されているため、
    # 必要に応じてルームごとの履歴を管理する場合は実装が必要
    # 現在はシンプルに現在のチャット履歴を使用
    # chat_stepもリセット
    if 'chat_step' not in st.session_state:
        st.session_state['chat_step'] = 'upload'


if __name__ == "__main__":
    main()
