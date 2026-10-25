# 青い箱の中心座標を取得（2.0, 2.0）
blue_box_x, blue_box_y = get_object_position("blue_box")

# 青い箱の裏側（スタート地点から見て反対側）に回り込むため、
# ロボットの胴体が箱にぶつからないように、十分な距離を確保する
# ロボットの前後方向に0.35mの余裕、左右に0.15mの余裕を考慮

# 青い箱の裏側は、青い箱の中心から -x 方向に0.7m（ロボットの長さ）離れた位置
# さらに、ロボットの前後方向に0.35mの安全距離を確保 → 2.0 - 0.7 - 0.35 = 0.95
target_x = blue_box_x - 0.7 - 0.35  # 安全距離を考慮
target_y = blue_box_y

# ロボットが目標位置に到達するまで、安全な速度で移動（左右は0）
current_x, current_y = get_position()
max_steps = 300
step_duration = 0.1
for step in range(max_steps):
    current_x, current_y = get_position()
    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    # 距離が0.1m以下なら到達
    if distance < 0.1:
        break
        
    # 速度を距離に応じて調整（最大0.5 m/s）
    vx = min(0.5, 0.5 * distance / 0.5)  # 0.5 m/s でゆっくり進む
    walk(vx, 0.0, 0.0, duration=step_duration)

# 到達後、青い箱の方向（+y 方向）を向く
target_yaw = 90.0  # +y 方向（青い箱の方向）
current_yaw = get_yaw()

# ターゲットに近づくまで旋回（最大200ステップで制限）
for step in range(200):
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    # 旋回速度をエラーに応じて調整（0.3以上で安定）
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 最終的に止まる
stop(0.5)
