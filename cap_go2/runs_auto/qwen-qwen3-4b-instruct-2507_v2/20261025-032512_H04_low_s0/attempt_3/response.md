```python
# 赤い箱まで行って、停滞（物体にぶつかる）を防ぐために、障害物の距離を常に確認し、安全な速度で前進する
# 初期位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標位置：赤い箱の中心
target_x, target_y = get_object_position("red_box")

# 障害物の安全距離設定（ロボットの大きさを考慮）
# 前後：0.35m（胴体の中心から壁の中心まで）
# 左右：0.15m（左右幅の半分）
# wall_back: (3.0, 0.0), 0.3×2.7
# wall_left: (2.325, 1.2), 1.65×0.3
# wall_right: (2.325, -1.2), 1.65×0.3

# 1. 初期の向き調整：赤い箱に向かって旋回（最大10ステップで終了）
target_yaw = math.degrees(math.atan2(target_y - y0, target_x - x0))
for _ in range(10):
    current_yaw = get_yaw()
    err_yaw = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err_yaw) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err_yaw)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 2. 安全な経路で前進（最大50ステップ、5秒以内）
max_steps = 50
step_duration = 0.2  # 高速で進むのではなく、安全に進むため、短いステップで確認
for step in range(max_steps):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 目標点へのベクトル
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.hypot(dx, dy)
    
    # 前進速度を調整（0.5 m/s で安全）
    vx = 0.5
    vy = 0.0
    
    # 各障害物との距離を確認（安全距離を守る）
    wall_back_dist = distance_to(3.0, 0.0)
    wall_left_dist = distance_to(2.325, 1.2)
    wall_right_dist = distance_to(2.325, -1.2)
    
    # 障害物に近づかないように、安全距離を守る
    if wall_back_dist < 0.35:
        # 前進不可 → 前進をやめる
        break
    if wall_left_dist < 0.15:
        # 左側に近づいた → 左にずらす
        vy = 0.3
        vx = 0.0
    if wall_right_dist < 0.15:
        # 右側に近づいた → 右にずらす
        vy = -0.3
        vx = 0.0
    
    # 前進（ステップ幅を大きくして、1ステップで安全な距離を確保）
    walk(vx, vy, 0.0, duration=step_duration)
    
    # 到達判定（0.5m以内なら終了）
    if distance_to_target <= 0.5:
        break

# 3. 到達後、短時間で止める（停滞を防ぐ）
stop(0.5)
```