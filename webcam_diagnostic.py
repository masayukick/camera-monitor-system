import cv2
import time
import subprocess
import os
import sys

def check_camera_privacy_settings():
    """
    Windowsのカメラプライバシー設定を確認する指示を表示
    """
    print("=== Windowsカメラプライバシー設定確認 ===")
    print("1. Windows設定を開く（Win + I）")
    print("2. 「プライバシーとセキュリティ」→「カメラ」")
    print("3. 以下の設定を確認：")
    print("   - 「カメラへのアクセス」がオンになっているか")
    print("   - 「アプリがカメラにアクセスすることを許可する」がオンになっているか")
    print("   - 「デスクトップアプリがカメラにアクセスすることを許可する」がオンになっているか")
    print()

def check_camera_usage():
    """
    カメラを使用中のプロセスをチェック
    """
    print("=== カメラ使用中アプリ確認 ===")
    print("以下のアプリが起動していないか確認してください：")
    apps_to_check = [
        "Zoom", "Microsoft Teams", "Skype", "Discord", "OBS Studio",
        "WebEx", "Google Meet", "カメラ（Windows標準）", "LINE"
    ]
    
    for app in apps_to_check:
        print(f"- {app}")
    
    print("\nタスクマネージャー（Ctrl + Shift + Esc）で確認できます")
    print()

def test_different_backends():
    """
    異なるOpenCVバックエンドでテスト
    """
    print("=== 異なるバックエンドでテスト ===")
    
    # 利用可能なバックエンド
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Microsoft Media Foundation"),
        (cv2.CAP_V4L2, "Video4Linux2"),
        (cv2.CAP_ANY, "Auto")
    ]
    
    for backend_id, backend_name in backends:
        print(f"\n{backend_name} バックエンドをテスト中...")
        
        try:
            cap = cv2.VideoCapture(0, backend_id)
            
            if cap.isOpened():
                print(f"✅ {backend_name}: 接続成功")
                
                # フレーム取得テスト
                ret, frame = cap.read()
                if ret:
                    print(f"✅ {backend_name}: フレーム取得成功")
                    print(f"   解像度: {frame.shape}")
                    cap.release()
                    return backend_id, backend_name
                else:
                    print(f"❌ {backend_name}: フレーム取得失敗")
                
                cap.release()
            else:
                print(f"❌ {backend_name}: 接続失敗")
                
        except Exception as e:
            print(f"❌ {backend_name}: エラー - {e}")
    
    return None, None

def test_windows_camera_app():
    """
    Windowsカメラアプリの動作確認を促す
    """
    print("=== Windowsカメラアプリテスト ===")
    print("1. Windowsキーを押して「カメラ」と入力")
    print("2. カメラアプリを起動")
    print("3. 正常に映像が表示されるかチェック")
    print()
    
    response = input("Windowsカメラアプリは正常に動作しましたか？ (y/n): ")
    return response.lower() in ['y', 'yes', 'はい']

def test_with_working_backend(backend_id, backend_name):
    """
    動作するバックエンドでフルテスト
    """
    print(f"\n=== {backend_name}バックエンドでフルテスト ===")
    
    cap = cv2.VideoCapture(0, backend_id)
    
    if not cap.isOpened():
        print("❌ カメラ接続失敗")
        return False
    
    # カメラ設定を調整
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # ウォームアップ
    print("カメラウォームアップ中...")
    for _ in range(5):
        cap.read()
        time.sleep(0.1)
    
    # フレーム取得テスト
    success_count = 0
    total_frames = 10
    
    print("フレーム取得テスト中...")
    for i in range(total_frames):
        ret, frame = cap.read()
        if ret:
            success_count += 1
            print(f"フレーム {i+1}: ✅")
        else:
            print(f"フレーム {i+1}: ❌")
        time.sleep(0.1)
    
    success_rate = (success_count / total_frames) * 100
    print(f"\n成功率: {success_rate:.1f}%")
    
    cap.release()
    
    return success_rate >= 80

def check_camera_drivers():
    """
    カメラドライバーの確認
    """
    print("=== カメラドライバー確認 ===")
    print("1. デバイスマネージャーを開く（Win + X → デバイスマネージャー）")
    print("2. 「イメージング デバイス」または「カメラ」を展開")
    print("3. c922 Pro Stream Webcam を右クリック")
    print("4. 「ドライバーの更新」を選択")
    print("5. 「ドライバーを自動的に検索」を選択")
    print()

def advanced_troubleshooting():
    """
    高度なトラブルシューティング
    """
    print("=== 高度なトラブルシューティング ===")
    print("1. カメラの物理的な確認：")
    print("   - USBケーブルの再接続")
    print("   - 別のUSBポートに接続")
    print("   - USBハブを使用している場合は直接PCに接続")
    print()
    print("2. システム再起動:")
    print("   - PCを再起動してテスト")
    print()
    print("3. 管理者権限でのテスト:")
    print("   - PowerShellを管理者として実行")
    print("   - スクリプトを再実行")
    print()

def main():
    """
    メイン診断フロー
    """
    print("🔍 Webカメラ問題診断ツール")
    print("=" * 40)
    
    # Step 1: プライバシー設定確認
    check_camera_privacy_settings()
    input("プライバシー設定を確認したらEnterを押してください...")
    
    # Step 2: 使用中アプリ確認
    check_camera_usage()
    input("カメラ使用中アプリを確認したらEnterを押してください...")
    
    # Step 3: Windowsカメラアプリテスト
    windows_camera_works = test_windows_camera_app()
    
    if not windows_camera_works:
        print("❌ Windowsカメラアプリが動作しない場合:")
        check_camera_drivers()
        advanced_troubleshooting()
        return
    
    print("✅ Windowsカメラアプリが動作している場合、OpenCVの問題の可能性があります")
    
    # Step 4: 異なるバックエンドでテスト
    working_backend, backend_name = test_different_backends()
    
    if working_backend is not None:
        print(f"\n✅ {backend_name}バックエンドで動作しました！")
        
        # フルテスト実行
        if test_with_working_backend(working_backend, backend_name):
            print("🎉 カメラは正常に動作しています！")
            
            # 推奨設定を表示
            print(f"\n📋 今後は以下のコードを使用してください:")
            print(f"cap = cv2.VideoCapture(0, {working_backend})  # {backend_name}")
        else:
            print("⚠️ 一部問題があります。さらなる調査が必要です。")
    else:
        print("❌ すべてのバックエンドで失敗しました")
        advanced_troubleshooting()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n診断が中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
