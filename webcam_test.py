import cv2
import sys
import time

def test_webcam():
    """
    Webカメラの動作テストを実行
    """
    print("=== Webカメラ動作テスト ===")
    
    # カメラの初期化を試行
    print("カメラに接続中...")
    cap = cv2.VideoCapture(0)  # 通常は0が最初のカメラ
    
    # カメラが正常に開けるかチェック
    if not cap.isOpened():
        print("❌ エラー: カメラにアクセスできません")
        # 他のインデックスも試行
        for i in range(1, 5):
            print(f"カメラインデックス {i} を試行中...")
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"✅ カメラインデックス {i} で接続成功")
                break
        else:
            print("❌ 利用可能なカメラが見つかりません")
            return False
    else:
        print("✅ カメラ接続成功")
    
    # カメラの基本情報を取得
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"解像度: {width} x {height}")
    print(f"FPS: {fps}")
    
    # フレーム取得テスト
    print("\nフレーム取得テスト開始...")
    frame_count = 0
    success_count = 0
    start_time = time.time()
    
    # 10フレーム取得を試行
    for i in range(10):
        ret, frame = cap.read()
        frame_count += 1
        
        if ret:
            success_count += 1
            print(f"フレーム {i+1}: ✅ 正常取得 (サイズ: {frame.shape})")
        else:
            print(f"フレーム {i+1}: ❌ 取得失敗")
        
        time.sleep(0.1)  # 100ms待機
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 結果表示
    print(f"\n=== テスト結果 ===")
    print(f"総フレーム数: {frame_count}")
    print(f"成功フレーム数: {success_count}")
    print(f"成功率: {(success_count/frame_count)*100:.1f}%")
    print(f"実測FPS: {frame_count/elapsed_time:.1f}")
    
    # カメラリソースを解放
    cap.release()
    
    # 判定
    if success_count >= 8:  # 80%以上成功
        print("🎉 カメラは正常に動作しています！")
        return True
    else:
        print("⚠️  カメラに問題がある可能性があります")
        return False

def live_preview_test():
    """
    リアルタイムプレビューテスト（オプション）
    """
    print("\n=== リアルタイムプレビューテスト ===")
    print("ESCキーで終了します")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ カメラにアクセスできません")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ フレーム取得に失敗しました")
            break
        
        # フレームに情報を表示
        cv2.putText(frame, 'Press ESC to exit', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Resolution: {frame.shape[1]}x{frame.shape[0]}', 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Webcam Test', frame)
        
        # ESCキーで終了
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ プレビューテスト完了")

def detailed_camera_info():
    """
    カメラの詳細情報を取得
    """
    print("\n=== カメラ詳細情報 ===")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ カメラにアクセスできません")
        return
    
    # 各種プロパティを取得
    properties = {
        'CAP_PROP_FRAME_WIDTH': cv2.CAP_PROP_FRAME_WIDTH,
        'CAP_PROP_FRAME_HEIGHT': cv2.CAP_PROP_FRAME_HEIGHT,
        'CAP_PROP_FPS': cv2.CAP_PROP_FPS,
        'CAP_PROP_BRIGHTNESS': cv2.CAP_PROP_BRIGHTNESS,
        'CAP_PROP_CONTRAST': cv2.CAP_PROP_CONTRAST,
        'CAP_PROP_SATURATION': cv2.CAP_PROP_SATURATION,
        'CAP_PROP_HUE': cv2.CAP_PROP_HUE,
        'CAP_PROP_GAIN': cv2.CAP_PROP_GAIN,
        'CAP_PROP_EXPOSURE': cv2.CAP_PROP_EXPOSURE,
    }
    
    for prop_name, prop_id in properties.items():
        value = cap.get(prop_id)
        print(f"{prop_name}: {value}")
    
    cap.release()

if __name__ == "__main__":
    try:
        # 基本動作テスト
        is_working = test_webcam()
        
        if is_working:
            # 詳細情報表示
            detailed_camera_info()
            
            # ユーザーにプレビューテストを確認
            response = input("\nリアルタイムプレビューテストを実行しますか？ (y/n): ")
            if response.lower() in ['y', 'yes', 'はい']:
                live_preview_test()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("OpenCVがインストールされているか確認してください: pip install opencv-python")
    finally:
        print("\nテスト完了")