import cv2
import numpy as np
import time
import platform
import subprocess
import datetime
import os

def ensure_dir(directory):
    """ディレクトリが存在することを確認し、存在しない場合は作成する"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"ディレクトリを作成しました: {directory}")
    return directory

def close_camera_app():
    """カメラアプリを閉じる（Windowsのみ）"""
    if platform.system() == 'Windows':
        try:
            print("カメラアプリを閉じています...")
            # タスクキルコマンドを使用してカメラアプリを終了
            subprocess.run(['taskkill', '/f', '/im', 'WindowsCamera.exe'], 
                          capture_output=True, text=True)
            time.sleep(2)  # カメラリソースが解放されるのを待つ
            print("カメラアプリを閉じました")
        except Exception as e:
            print(f"カメラアプリを閉じる際にエラーが発生しました: {e}")

def get_camera_list():
    """システムに接続されているカメラのリストを取得する"""
    camera_list = []
    
    # Windowsの場合
    if platform.system() == 'Windows':
        try:
            # WMICコマンドを使用してカメラデバイスを取得
            result = subprocess.run(
                ['wmic', 'path', 'Win32_PnPEntity', 'where', "PNPClass='Image'", 'get', 'Name,Status'],
                capture_output=True, text=True, check=True
            )
            
            lines = result.stdout.strip().split('\n')
            # ヘッダー行をスキップ
            for line in lines[1:]:
                if line.strip():
                    # 名前とステータスを分離
                    parts = line.strip().split('  ')
                    if len(parts) >= 1:
                        name = parts[0].strip()
                        status = "OK" if len(parts) > 1 else "Unknown"
                        camera_list.append((name, status))
            
            print(f"検出されたカメラデバイス: {len(camera_list)}")
            for i, (name, status) in enumerate(camera_list):
                print(f"  {i}: {name} ({status})")
        
        except Exception as e:
            print(f"カメラリストの取得中にエラーが発生しました: {e}")
    
    return camera_list

def is_white_cat_plush(frame):
    """
    画像内に白い猫のぬいぐるみが映っているかどうかを判断する
    
    Parameters:
    - frame: 分析するフレーム
    
    Returns:
    - is_cat: 白い猫のぬいぐるみが映っていると判断された場合はTrue
    - confidence: 信頼度（0.0〜1.0）
    - details: 詳細情報（デバッグ用）
    """
    # フレームがNoneの場合はFalseを返す
    if frame is None:
        return False, 0.0, "フレームがありません"
    
    # フレームのサイズを取得
    height, width = frame.shape[:2]
    
    # HSV色空間に変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 白色の範囲を定義（HSV色空間）- さらに広い範囲に調整
    # 白色は彩度が低く、明度が高い
    lower_white = np.array([0, 0, 150])  # 明度の下限をさらに下げる（180→150）
    upper_white = np.array([180, 80, 255])  # 彩度の上限をさらに上げる（50→80）
    
    # 白色のマスクを作成
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    
    # ノイズ除去のためのモルフォロジー演算
    kernel = np.ones((5, 5), np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
    
    # マスクを適用して白い部分だけを抽出
    white_result = cv2.bitwise_and(frame, frame, mask=white_mask)
    
    # 白色のピクセル数をカウント
    white_pixel_count = cv2.countNonZero(white_mask)
    white_percentage = white_pixel_count / (height * width) * 100
    
    # 輪郭を検出
    contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 大きな白色の塊があるかチェック
    large_white_regions = 0
    largest_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        largest_area = max(largest_area, area)
        if area > 5000:  # 閾値を上げる（3000→5000）
            large_white_regions += 1
    
    # 猫の形状に関する特徴を検出
    cat_shape_detected = False
    for contour in contours:
        if cv2.contourArea(contour) > 5000:
            # 輪郭の近似
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 猫の形状の特徴（丸みを帯びた形状）
            if len(approx) > 4:  # 多角形の頂点数が多い（丸みがある）- 条件をさらに緩和（6→4）
                cat_shape_detected = True
    
    # 判定ロジック - 閾値を調整
    # 1. 白色のピクセルが一定割合以上ある
    # 2. 大きな白色の塊が存在する
    # 3. 猫の形状の特徴がある
    is_cat = (white_percentage > 10 and  # 白色率の閾値を下げる（15→10）
              large_white_regions >= 1 and 
              cat_shape_detected)
    
    # 信頼度の計算（調整版）
    confidence = min(white_percentage / 20, 1.0) * 0.5  # 白色率の閾値変更に合わせて調整（30→20）
    if large_white_regions >= 1:
        confidence += 0.3
    if cat_shape_detected:
        confidence += 0.2
    
    details = {
        "white_percentage": white_percentage,
        "large_white_regions": large_white_regions,
        "largest_area": largest_area,
        "cat_shape_detected": cat_shape_detected,
        "confidence": confidence
    }
    
    return is_cat, confidence, details

def monitor_camera(interval=2.0, duration=None, camera_index=0, camera_name=None, 
                  resolution=(640, 360), log_dir="camera_logs", save_alerts=True):
    """
    カメラを定期的に監視し、白い猫のぬいぐるみが映っているかどうかを判断する
    
    Parameters:
    - interval: チェック間隔（秒）
    - duration: 監視時間（秒）、Noneの場合は無限に監視
    - camera_index: カメラデバイス番号
    - camera_name: カメラ名（指定された場合はカメラインデックスよりも優先）
    - resolution: 解像度（幅, 高さ）
    - log_dir: ログを保存するディレクトリ
    - save_alerts: 異常検知時に画像を保存するかどうか
    """
    # カメラアプリを閉じる
    close_camera_app()
    
    # ログディレクトリを確保
    log_dir = ensure_dir(log_dir)
    
    # 現在の日時を取得してサブディレクトリ名に使用
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(log_dir, f"session_{timestamp}")
    
    # カメラ名が指定されている場合、カメラインデックスを探す
    if camera_name is not None:
        camera_list = get_camera_list()
        for i, (name, _) in enumerate(camera_list):
            if camera_name.lower() in name.lower():
                print(f"カメラ名 '{camera_name}' に一致するデバイスを見つけました: {name}")
                camera_index = i
                break
    
    print(f"カメラ監視を開始します...")
    print(f"カメラデバイス: {camera_index}")
    print(f"解像度: {resolution[0]}x{resolution[1]}")
    print(f"チェック間隔: {interval}秒")
    if duration:
        print(f"監視時間: {duration}秒")
    else:
        print(f"監視時間: 無制限（Ctrl+Cで終了）")
    
    # カメラを初期化
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # DirectShowバックエンドを使用
    
    if not cap.isOpened():
        print(f"エラー: カメラを開くことができませんでした")
        return
    
    # カメラのプロパティを設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
    cap.set(cv2.CAP_PROP_FPS, 15)  # フレームレートを15fpsに設定
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # バッファサイズを1に設定
    
    # ウォームアップのためにいくつかのフレームを読み飛ばす
    print("カメラウォームアップ中...")
    for i in range(10):
        ret, _ = cap.read()
        if not ret:
            print(f"  ウォームアップ {i+1}/10 - フレーム取得失敗")
        time.sleep(0.2)
    
    print("カメラ監視を開始しました！")
    print("監視中... (ESCキーで終了、Ctrl+Cでも終了できます)")
    
    # 監視開始時間
    start_time = time.time()
    alert_count = 0
    normal_count = 0
    
    try:
        while True:
            # 経過時間をチェック
            elapsed_time = time.time() - start_time
            if duration and elapsed_time >= duration:
                print(f"指定された監視時間 {duration}秒 が経過しました")
                break
            
            # バッファをクリア
            for _ in range(5):
                cap.grab()
            
            # フレームを取得
            ret, frame = cap.read()
            
            if not ret:
                print("エラー: フレームの取得に失敗しました")
                time.sleep(interval)
                continue
            
            # 現在の時刻
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 白い猫のぬいぐるみが映っているかどうかを判断
            is_cat, confidence, details = is_white_cat_plush(frame)
            
            # 状態に応じて表示を変更（英語で表示）
            if is_cat:
                status = "Normal"  # 「監視中」を「Normal」に変更
                status_color = (0, 255, 0)  # 緑色
                normal_count += 1
            else:
                status = "Alert"  # 「異常」を「Alert」に変更
                status_color = (0, 0, 255)  # 赤色
                alert_count += 1
                
                # 異常検知時に画像を保存
                if save_alerts:
                    if not os.path.exists(session_dir):
                        os.makedirs(session_dir)
                    alert_filename = f"alert_{alert_count:03d}.jpg"
                    alert_filepath = os.path.join(session_dir, alert_filename)
                    cv2.imwrite(alert_filepath, frame)
                    print(f"異常を検知しました: {alert_filepath}")
            
            # フレームに情報を追加（英語で表示して文字化けを防止）
            cv2.putText(frame, f"Status: {status} ({confidence:.2f})", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(frame, f"Time: {current_time}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"White %: {details['white_percentage']:.1f}%", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"White regions: {details['large_white_regions']} (Max area: {details['largest_area']})", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Cat shape: {details['cat_shape_detected']}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # マスク画像も表示（デバッグ用）
            try:
                # is_white_cat_plush関数から白色マスクを取得する必要があるため、再度計算
                height, width = frame.shape[:2]
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                lower_white = np.array([0, 0, 150])  # 明度の下限をさらに下げる（180→150）
                upper_white = np.array([180, 80, 255])  # 彩度の上限をさらに上げる（50→80）
                white_mask = cv2.inRange(hsv, lower_white, upper_white)
                kernel = np.ones((5, 5), np.uint8)
                white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
                white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
                
                # 輪郭を検出して描画
                contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contour_mask = np.zeros_like(white_mask)
                cat_shape_detected = False
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 5000:  # 一定以上の大きさの輪郭のみ描画
                        cv2.drawContours(contour_mask, [contour], -1, 255, -1)
                        
                        # 猫の形状の特徴を検出
                        epsilon = 0.02 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        if len(approx) > 4:  # 多角形の頂点数が多い（丸みがある）- 条件をさらに緩和（6→4）
                            cat_shape_detected = True
                
                # マスク画像をリサイズして表示（右下に小さく表示）
                white_mask_display = cv2.cvtColor(white_mask, cv2.COLOR_GRAY2BGR)
                contour_mask_display = cv2.cvtColor(contour_mask, cv2.COLOR_GRAY2BGR)
                
                # 輪郭を色付けして表示
                contour_mask_color = np.zeros_like(contour_mask_display)
                contour_mask_color[:,:,0] = 0    # B
                contour_mask_color[:,:,1] = 0    # G
                contour_mask_color[:,:,2] = contour_mask  # R
                
                # マスク画像と輪郭画像を合成
                combined_mask = cv2.addWeighted(white_mask_display, 0.7, contour_mask_color, 0.3, 0)
                
                mask_height, mask_width = 180, 320
                mask_small = cv2.resize(combined_mask, (mask_width, mask_height))
                
                # 画像の右下にマスク画像を配置
                if height >= mask_height and width >= mask_width:
                    frame[height-mask_height:height, width-mask_width:width] = mask_small
                    
                    # マスク画像の境界線を描画
                    cv2.rectangle(frame, (width-mask_width, height-mask_height), 
                                 (width, height), (0, 255, 255), 2)
                    
                    # マスク画像のタイトルを表示（英語で表示）
                    cv2.putText(frame, "Mask Image", (width-mask_width+10, height-mask_height+20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            except Exception as e:
                print(f"マスク画像の表示中にエラーが発生しました: {e}")
            
            # フレームを表示
            cv2.imshow('C922 Pro Stream Webcam 監視', frame)
            
            # 監視状態をコンソールに表示（定期的に）
            if int(elapsed_time) % 10 == 0 and int(elapsed_time) > 0:
                if is_cat:
                    print(f"監視中... 経過時間: {int(elapsed_time)}秒 - 状態: 正常 (白い猫のぬいぐるみを検出)")
                else:
                    print(f"監視中... 経過時間: {int(elapsed_time)}秒 - 状態: 異常 (白い猫のぬいぐるみを検出できません)")
            
            # キー入力をチェック
            key = cv2.waitKey(1)
            
            # ESCキーで終了
            if key == 27:  # ESCキー
                print("監視を中断しました")
                break
            
            # 次のチェックまで待機
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n監視が中断されました（Ctrl+C）")
    
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
    
    finally:
        # リソースを解放
        if cap is not None:
            cap.release()
        
        cv2.destroyAllWindows()
        
        # 監視結果を表示
        elapsed_time = time.time() - start_time
        total_checks = normal_count + alert_count
        
        print("\n===== 監視結果 =====")
        print(f"監視時間: {elapsed_time:.1f}秒")
        print(f"チェック回数: {total_checks}回")
        print(f"正常: {normal_count}回 ({normal_count/total_checks*100:.1f}%)")
        print(f"異常: {alert_count}回 ({alert_count/total_checks*100:.1f}%)")
        
        if alert_count > 0 and save_alerts:
            print(f"異常検知画像の保存先: {session_dir}")

if __name__ == "__main__":
    print("C922 Pro Stream Webcam 監視ツール")
    
    # カメラリストを取得
    camera_list = get_camera_list()
    camera_name = None
    
    # C922 Pro Stream Webcamを探す
    for name, _ in camera_list:
        if "C922" in name:
            camera_name = name
            print(f"\nC922 Pro Stream Webcamが見つかりました: {camera_name}")
            break
    
    try:
        print("\n以下のオプションから選択してください:")
        print("1. 通常監視モード")
        print("2. 白色検出パラメータ調整モード")
        
        choice = input("\n選択してください (1-2): ") or "1"
        
        if choice == "2":
            print("\n白色検出パラメータ調整モード")
            print("このモードでは、白色検出のパラメータを調整できます")
            
            # HSV値の調整
            h_min = int(input("色相(H)の最小値 [0-180, デフォルト: 0]: ") or "0")
            h_max = int(input("色相(H)の最大値 [0-180, デフォルト: 180]: ") or "180")
            s_min = int(input("彩度(S)の最小値 [0-255, デフォルト: 0]: ") or "0")
            s_max = int(input("彩度(S)の最大値 [0-255, デフォルト: 60]: ") or "60")
            v_min = int(input("明度(V)の最小値 [0-255, デフォルト: 150]: ") or "150")
            v_max = int(input("明度(V)の最大値 [0-255, デフォルト: 255]: ") or "255")
            
            # 白色率の閾値
            white_threshold = float(input("白色率の閾値 [デフォルト: 10.0]: ") or "10.0")
            
            # 白色領域の面積閾値
            area_threshold = int(input("白色領域の面積閾値 [デフォルト: 3000]: ") or "3000")
            
            # HSV値を配列に設定
            lower_white = np.array([h_min, s_min, v_min])
            upper_white = np.array([h_max, s_max, v_max])
            
            # 監視間隔（秒）
            interval = float(input("\nチェック間隔（秒）を入力してください [デフォルト: 2.0]: ") or "2.0")
            
            # 監視時間（秒）
            duration_input = input("監視時間（秒）を入力してください [無制限の場合は空欄]: ")
            duration = float(duration_input) if duration_input else None
            
            # 異常検知時に画像を保存するかどうか
            save_alerts_input = input("異常検知時に画像を保存しますか？ (y/n) [デフォルト: y]: ") or "y"
            save_alerts = save_alerts_input.lower() == "y"
            
            # カスタムパラメータでモニター関数を定義
            def custom_is_white_cat_plush(frame):
                if frame is None:
                    return False, 0.0, "フレームがありません"
                
                height, width = frame.shape[:2]
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # カスタムHSV値を使用
                white_mask = cv2.inRange(hsv, lower_white, upper_white)
                
                kernel = np.ones((5, 5), np.uint8)
                white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
                white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
                
                white_result = cv2.bitwise_and(frame, frame, mask=white_mask)
                white_pixel_count = cv2.countNonZero(white_mask)
                white_percentage = white_pixel_count / (height * width) * 100
                
                contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                large_white_regions = 0
                largest_area = 0
                
                # 猫の形状に関する特徴を検出
                cat_shape_detected = False
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    largest_area = max(largest_area, area)
                    if area > area_threshold:
                        large_white_regions += 1
                        
                        # 輪郭の近似
                        epsilon = 0.02 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        
                        # 猫の形状の特徴（丸みを帯びた形状）
                        if len(approx) > 4:  # 多角形の頂点数が多い（丸みがある）- 条件をさらに緩和（6→4）
                            cat_shape_detected = True
                
                # 判定ロジック - 閾値を調整
                # 1. 白色のピクセルが一定割合以上ある
                # 2. 大きな白色の塊が存在する
                # 3. 猫の形状の特徴がある
                is_cat = (white_percentage > white_threshold and 
                          large_white_regions >= 1 and 
                          cat_shape_detected)
                
                # 信頼度の計算（調整版）
                confidence = min(white_percentage / (white_threshold * 2.5), 1.0) * 0.5
                if large_white_regions >= 1:
                    confidence += 0.3
                if cat_shape_detected:
                    confidence += 0.2
                
                details = {
                    "white_percentage": white_percentage,
                    "large_white_regions": large_white_regions,
                    "largest_area": largest_area,
                    "cat_shape_detected": cat_shape_detected,
                    "confidence": confidence
                }
                
                return is_cat, confidence, details
            
            # オリジナル関数を保存
            original_is_white_cat_plush = is_white_cat_plush
            
            # カスタム関数に置き換え
            is_white_cat_plush = custom_is_white_cat_plush
            
            # カメラ監視を開始
            if camera_name:
                monitor_camera(interval=interval, duration=duration, camera_name=camera_name, save_alerts=save_alerts)
            else:
                monitor_camera(interval=interval, duration=duration, save_alerts=save_alerts)
            
            # 元の関数に戻す
            is_white_cat_plush = original_is_white_cat_plush
        else:
            # 通常監視モード
            # 監視間隔（秒）
            interval = float(input("チェック間隔（秒）を入力してください [デフォルト: 2.0]: ") or "2.0")
            
            # 監視時間（秒）
            duration_input = input("監視時間（秒）を入力してください [無制限の場合は空欄]: ")
            duration = float(duration_input) if duration_input else None
            
            # 異常検知時に画像を保存するかどうか
            save_alerts_input = input("異常検知時に画像を保存しますか？ (y/n) [デフォルト: y]: ") or "y"
            save_alerts = save_alerts_input.lower() == "y"
            
            # カメラ監視を開始
            if camera_name:
                monitor_camera(interval=interval, duration=duration, camera_name=camera_name, save_alerts=save_alerts)
            else:
                monitor_camera(interval=interval, duration=duration, save_alerts=save_alerts)
    
    except KeyboardInterrupt:
        print("\nプログラムが中断されました")
    
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
    
    finally:
        print("\nプログラムを終了します")
        cv2.destroyAllWindows()
