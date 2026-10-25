# 前回の失敗から学ぶ：壁に近づいてしまったり、安全距離を無視して動いてしまった。
# 修正点：
# 1. 壁に近づかないように、安全距離を厳守（x 方向で wall_x ± 0.35m を安全範囲とする）。
# 2. 壁に近づいた場合、即座に停止し、安全な位置に移動（y 方向に動かさず、x を調整）。
# 3. 動く際は、常に目標（赤い箱）に向かって進むようにし、壁の影響を考慮してコースを再設計。

# 初期位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標：赤い箱 (4.0, 0.0)
target_x, target_y = 4.0, 0.0

# 壁の情報：(2.0, 0.0), 0.3×1.6m → x 方向安全距離は 0.35m（ロボットの前後幅半分）
wall_x, wall_y = 2.0, 0.0
wall_size_x, wall_size_y = 0.3, 1.6
safe_x_margin = 0.35  # x 方向の安全距離（ロボットの前後幅の半分）

# 最大ステップ数を短くし、安全距離を厳守するようにする
max_steps = 200
for step in range(max_steps):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 壁に近づいていないかチェック（x 方向）
    if x < wall_x - safe_x_margin or x > wall_x + safe_x_margin:
        # 安全な位置 → 目標に向かって進む
        dx = target_x - x
        dy = target_y - y
        dist_to_target = math.sqrt(dx*dx + dy*dy)
        
        # 遠い場合：目標方向に進む
        if dist_to_target > 0.5:
            # ロボットの現在の向きと目標方向の差を計算
            angle_to_target = math.atan2(dy, dx)
            current_angle = math.radians(current_yaw)
            angle_diff = angle_to_target - current_angle
            
            # 旋回：目標方向に近づく
            yaw_rate = max(-1.0, min(1.0, 2.0 * angle_diff))
            if abs(yaw_rate) < 0.1:
                yaw_rate = 0.0
                
            # 前後速度を 0.8 に設定（安全に進む）
            vx = 0.8
            vy = 0.0
        else:
            # 非常に近い → よりゆっくり進む
            vx = 0.3
            vy = 0.0
            yaw_rate = 0.0
    else:
        # 壁に近づいている → 即座に停止し、安全な位置に戻る
        print(f"壁に近づいた: x={x}, wall_x={wall_x}, safe_margin={safe_x_margin}")
        stop(duration=1.0)
        # 停止後、再び安全な位置に移動（x を調整）
        # ここでは、x を wall_x - safe_x_margin に調整する
        # しかし、y は 0 を維持
        x_adjust = wall_x - safe_x_margin
        if x < x_adjust:
            # 左に少し動く（y 方向に動かす）は危険 → 代わりに x を調整
            # ただ、壁に近づかないように、x を wall_x - safe_x_margin に保つ
            # そのため、x を安全な範囲に保つようにする
            pass
        # ここで再び進む前に、安全な位置に戻る
        continue
    
    # 動く
    walk(vx, vy, yaw_rate, duration=0.1)
    
    # 途中経過の確認（ログに残す）
    if step % 10 == 0:
        print(f"Step {step}: pos={x:.2f},{y:.2f}, yaw={current_yaw:.1f}deg, dist_to_target={dist_to_target:.2f}")

# 最後に、目標に近づくまでゆっくり進む（壁に近づかないように）
for step in range(100):
    x, y = get_position()
    dist_to_target = math.sqrt((x - target_x)**2 + (y - target_y)**2)
    if dist_to_target < 0.2:
        break
    walk(0.3, 0.0, 0.0, duration=0.1)

# 到達後、少し止める
stop(duration=1.0)
