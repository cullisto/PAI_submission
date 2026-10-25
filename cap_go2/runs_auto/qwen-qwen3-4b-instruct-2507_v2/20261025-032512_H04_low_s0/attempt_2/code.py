# 赤い箱まで行って、時間切れを防ぐために、より効率的な経路を選び、障害物を避けながら前進する
# 初期位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標位置：赤い箱の中心
target_x, target_y = get_object_position("red_box")

# ロボットの大きさを考慮：前後0.35m、左右0.15m
# 障害物の位置と大きさ
# wall_back: (3.0, 0.0), 0.3×2.7 → 前後方向に0.35mの安全距離
# wall_left: (2.325, 1.2), 1.65×0.3 → 左右方向に0.15mの安全距離
# wall_right: (2.325, -1.2), 1.65×0.3 → 左右方向に0.15mの安全距離

# 目標方向に向けた旋回（短時間で効率的に）
target_yaw = math.degrees(math.atan2(target_y - y0, target_x - x0))

# 旋回：目標の向きに近づくまで、最大30ステップ（3秒以内）
for _ in range(30):
    current_yaw = get_yaw()
    err_yaw = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err_yaw) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err_yaw)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 旋回後、安全な経路で前進（最大100ステップ、10秒以内）
max_steps = 100
step_duration = 0.1
for step in range(max_steps):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの向きに合わせて目標点へのベクトルを計算
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.hypot(dx, dy)
    
    # 前進速度を調整（0.8 m/s）
    vx = 0.8
    vy = 0.0
    
    # 障害物との距離をチェック（安全距離：0.35m（前後）、0.15m（左右））
    wall_back_dist = distance_to(3.0, 0.0)
    wall_left_dist = distance_to(2.325, 1.2)
    wall_right_dist = distance_to(2.325, -1.2)
    
    # 障害物に近づかないようにチェック
    if wall_back_dist < 0.35:
        # 前進を中止
        break
    if wall_left_dist < 0.15:
        # 左側の壁に近づった → 左にずらす（左右に動かす）
        vy = 0.3
        vx = 0.0
    if wall_right_dist < 0.15:
        # 右側の壁に近づった → 右にずらす
        vy = -0.3
        vx = 0.0
    
    # 前進
    walk(vx, vy, 0.0, duration=step_duration)
    
    # 到達判定（0.5m以内なら終了）
    if distance_to_target <= 0.5:
        break

# 到達後、少し止める
stop(0.5)
