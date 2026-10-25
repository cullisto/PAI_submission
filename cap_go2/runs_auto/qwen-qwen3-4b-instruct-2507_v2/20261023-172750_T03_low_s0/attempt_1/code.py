# 赤い箱の中心位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 赤い箱までの距離を計算（ロボットの中心から）
target_distance = math.sqrt((red_box_x - x0) ** 2 + (red_box_y - y0) ** 2)

# ロボットが赤い箱に近づくまで前進する（障害物との距離を考慮して安全に移動）
# まず、ロボットの向きを赤い箱に向ける
for _ in range(300):  # 最大 30 秒
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    # 目標方向へのベクトル（x, y）を計算
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 向きの誤差を計算（-180〜180度の範囲で）
    yaw_err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    
    # 旋回の角速度を計算（誤差が小さい場合はゆっくり）
    if abs(yaw_err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    
    # 旋回を実行
    walk(0.0, 0.0, rate, duration=0.1)

# 向きが正しい状態で、赤い箱まで安全に近づく
# 安全な距離（ロボットの前後方向に0.35m、左右に0.15m）を考慮して、目標までの距離を計算
safe_distance = 0.35  # 前後方向の安全距離（胴体の半分）
max_approach_distance = target_distance - safe_distance

# 最大で max_approach_distance だけ近づく
for _ in range(300):  # 最大 30 秒
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    # 赤い箱までの距離
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    dist = math.sqrt(dx**2 + dy**2)
    
    # 安全な距離を超えないように、移動速度を制限
    if dist <= safe_distance:
        break
    
    # 前進速度を調整（距離に応じてスケーリング）
    vx = min(1.0, max(-0.5, 0.5 * (max_approach_distance / dist)))
    walk(vx, 0.0, 0.0, duration=0.1)

# 最終的に赤い箱に到達したことを確認し、止まる
stop(1.0)
