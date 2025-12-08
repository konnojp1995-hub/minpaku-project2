"""
Tesseractテストスクリプト（簡易版）
"""
import os

# Tesseractのパスを確認
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
print(f"Tesseractパス: {tesseract_path}")
print(f"ファイル存在確認: {os.path.exists(tesseract_path)}")

# pytesseractのインポートテスト
try:
    import pytesseract
    print("pytesseractのインポートに成功しました")
    
    # Tesseractのパスを設定
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    # バージョン確認
    try:
        version = pytesseract.get_tesseract_version()
        print(f"Tesseractバージョン: {version}")
    except Exception as e:
        print(f"バージョン取得エラー: {e}")
    
    # 簡単なテスト
    try:
        import numpy as np
        import cv2
        
        # テスト画像を作成
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, "Test", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # OCRテスト
        result = pytesseract.image_to_string(test_image, lang='eng')
        print(f"OCRテスト結果: '{result.strip()}'")
        
        print("Tesseractテストが成功しました！")
        
    except Exception as e:
        print(f"OCRテストエラー: {e}")
        
except ImportError as e:
    print(f"pytesseractのインポートに失敗しました: {e}")
    print("pytesseractをインストールしてください: pip install pytesseract")

# EasyOCRのテスト
try:
    import easyocr
    print("easyocrのインポートに成功しました")
    
    # EasyOCRリーダーを初期化
    reader = easyocr.Reader(['ja', 'en'])
    print("EasyOCRリーダーの初期化に成功しました")
    
except ImportError as e:
    print(f"easyocrのインポートに失敗しました: {e}")
    print("easyocrをインストールしてください: pip install easyocr")
except Exception as e:
    print(f"EasyOCR初期化エラー: {e}")

