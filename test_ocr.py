"""
Tesseractテストスクリプト
"""
import sys
import os

# モジュールのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

try:
    from modules.ocr_extractor import create_ocr_extractor
    print("OCRモジュールのインポートに成功しました")
    
    # OCR抽出器を作成
    ocr_extractor = create_ocr_extractor()
    
    print(f"Tesseract利用可能: {ocr_extractor.tesseract_available}")
    print(f"EasyOCR利用可能: {ocr_extractor.easyocr_available}")
    
    # Tesseractテスト
    if ocr_extractor.tesseract_available:
        print("\nTesseractテストを実行中...")
        tesseract_result = ocr_extractor.test_tesseract()
        print(f"Tesseractテスト結果: {tesseract_result}")
    else:
        print("\nTesseractは利用できません")
    
    # EasyOCRテスト
    if ocr_extractor.easyocr_available:
        print("\nEasyOCRテストを実行中...")
        easyocr_result = ocr_extractor.test_easyocr()
        print(f"EasyOCRテスト結果: {easyocr_result}")
    else:
        print("\nEasyOCRは利用できません")
        
except ImportError as e:
    print(f"モジュールのインポートに失敗しました: {e}")
except Exception as e:
    print(f"エラーが発生しました: {e}")

