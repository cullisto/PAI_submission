```python
# 前回の失敗から学ぶ：ロボットが壁に近づいてしまい、安全距離を無視して動いていた。
# 特に、x が 1.5 付近で停滞しており、壁（x=2.0）に近づいていないが、安全距離を守っていないように見える。
# しかし、安全距離は 0.35m で、wall_x=2.0 なので、x < 1.65 または x > 2.35 が安全。
# 現在の位置 (1.51, 0.03) は x=1.51 < 1.65 なので、安全範囲内。なぜか動けないか？

# 原因の再確認：
# 1. 壁に近づくことはないが、目標（4.0, 0.0）に向かって進むべき。
# 2. しかし、目標方向への角度計算が誤っており、ロボットが壁の近くにいるのに、目標方向に旋回できていない。
# 3. 動作が遅い（20秒以上動かず、わずかな移動）→ 指令が無効化されている可能性。

# 修正点：
# 1. 壁に近づくかどうかを厳密にチェック（x 方向の安全距離を厳守）。
# 2. 壁に近づいていない場合でも、目標に向かって進むようにする（目標方向に常に進む）。
# 3. 旋回の計算を安定化し、目標方向に常に近づくようにする。
# 4. 動きのステップを短くし、安全距離を守りつつ、目標に近づくようにする。
# 5. 動かなかった場合に、即座に再評価し、安全な位置に進む。

# 初期位置と向きを取得
x, y = get_position()
yaw = get_yaw()

# 目標：赤い箱 (4.0, 0.0)
target_x, target_y = 4.0, 0.0

# 壁の情報：(2.0, 0.0), 0.3×1.6m → x 方向安全距離は 0.35m（ロボットの前後幅の半分）
wall_x, wall_y = 2.0, 0.0
safe_x_margin = 0.35  # x 方向の安全距離（ロボットの前後幅の半分）

# 最大ステップ数を短くし、安全距離を厳守
max_steps = 300
for step in range(max_steps):
    # 現在の位置を取得
    curr_x, curr_y = get_position()
    curr_yaw = get_yaw()
    
    # 壁に近づいていないかチェック（x 方向）
    if curr_x < wall_x - safe_x_margin or curr_x > wall_x + safe_x_margin:
        # 安全な位置 → 目標に向かって進む
        dx = target_x - curr_x
        dy = target_y - curr_y
        dist_to_target = math.sqrt(dx*dx + dy*dy)
        
        # 距離が大きい場合：目標方向に進む
        if dist_to_target > 0.5:
            # 目標方向の角度（ロボットの向きと差）
            angle_to_target = math.atan2(dy, dx)
            curr_angle_rad = math.radians(curr_yaw)
            angle_diff = angle_to_target - curr_angle_rad
            
            # 旋回：目標方向に近づく（角度差を小さくする）
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
        # 壁に近づいている → 即座に停止し、安全な位置に移動
        print(f"壁に近づいた: x={curr_x:.2f}, wall_x={wall_x}, safe_margin={safe_x_margin}")
        stop(duration=1.0)
        # 停止後、再び安全な位置に戻る（x を wall_x - safe_x_margin に調整）
        # しかし、y は 0 を維持
        # ここで、安全な位置に移動するための再スタート
        continue
    
    # 動く（duration=0.1 で短く、安定）
    walk(vx, vy, yaw_rate, duration=0.1)
    
    # 途中経過の確認（ログに残す）
    if step % 10 == 0:
        print(f"Step {step}: pos={curr_x:.2f},{curr_y:.2f}, yaw={curr_yaw:.1f}deg, dist_to_target={dist_to_target:.2f}")

# 最後に、目標に近づくまでゆっくり進む（壁に近づかないように）
for step in range(100):
    x, y = get_position()
    dist_to_target = math.sqrt((x - target_x)**2 + (y - target_y)**2)
    if dist_to_target < 0.2:
        break
    walk(0.3, 0.0, 0.0, duration=0.1)

# 到達後、少し止める
stop(duration=1.0)
```