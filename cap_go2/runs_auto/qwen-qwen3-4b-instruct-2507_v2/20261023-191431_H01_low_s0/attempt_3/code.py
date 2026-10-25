# 青い箱の中心座標を取得（2.0, 2.0）
blue_box_x, blue_box_y = get_object_position("blue_box")

# 青い箱の裏側（スタート地点から見て反対側）に回り込むため、
# ロボットの安全距離を厳密に考慮（前後0.35m、左右0.15m）
# 目標位置：青い箱の中心から -x 方向にロボットの長さ（0.7m）を引いて、さらに0.35mの安全距離を確保
target_x = blue_box_x - 0.7 - 0.35  # x方向に安全に後ろに
target_y = blue_box_y              # y方向はそのまま

# 安全な移動ループ：距離が0.1m以下になるまで、前後に移動（左右0、速度制限0.5m/s）
current_x, current_y = get_position()
max_steps = 300
step_duration = 0.1

for step in range(max_steps):
    current_x, current_y = get_position()
    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    # 0.1m以内なら終了
    if distance < 0.1:
        break
        
    # 速度を距離に応じて調整（最大0.5 m/s、距離が小さいときは遅く）
    speed = min(0.5, 0.5 * distance / 0.3)  # 距離が小さいほど遅く
    walk(speed, 0.0, 0.0, duration=step_duration)
    
    # 毎ステップで位置を確認し、障害物に近づいていないかチェック（安全距離確保）
    # 障害物に近づいていないかを確認（距離が0.35m以下なら、安全ではない）
    # ただし、物体の座標を取得して、ロボットが物体にぶつからないようにする

# 障害物に近づくかどうかを確認（特に青い箱の周囲）
# もしロボットが青い箱に近づいていたら、安全な距離を再確認
# ただし、物体の座標を取得して、距離をチェック（安全距離0.35m以内なら、移動を中止）

# まず、青い箱の安全距離を確認（x方向に0.35m以上離れているか）
current_x, current_y = get_position()
dist_to_blue_box = math.sqrt((current_x - blue_box_x)**2 + (current_y - blue_box_y)**2)
if dist_to_blue_box < 0.35:
    # 青い箱に近すぎるので、安全な位置に戻る
    # より安全な位置に移動（x方向に0.7m後ろ、y方向は0）
    safe_x = blue_box_x - 0.7 - 0.35
    safe_y = 0.0
    # 0.1m以内に収まるまで移動
    for _ in range(300):
        current_x, current_y = get_position()
        dx = safe_x - current_x
        dy = safe_y - current_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.1:
            break
        walk(0.3, 0.0, 0.0, duration=0.1)

# 最後に青い箱の方向（+y 方向）を向く
target_yaw = 90.0
current_yaw = get_yaw()
for step in range(200):
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 最終的に止まる
stop(0.5)
