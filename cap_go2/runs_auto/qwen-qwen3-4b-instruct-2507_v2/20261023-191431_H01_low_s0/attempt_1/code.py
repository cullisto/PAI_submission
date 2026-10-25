# 青い箱の中心座標を取得（2.0, 2.0）
blue_box_x, blue_box_y = get_object_position("blue_box")

# 青い箱の裏側（スタート地点から見て反対側）は、青い箱の中心から -x 方向に移動した位置
# ロボットの大きさを考慮して、青い箱の中心から0.35m（前後方向）離れた位置に近づくようにする
# つまり、青い箱の裏側は (2.0 - 0.7, 2.0) に近い位置（ロボットの胴体の前後に0.35mの余裕があるように）

# 目標位置を設定：青い箱の裏側（x方向に少し後ろに）
target_x = blue_box_x - 0.7 - 0.35  # 箱の中心からロボットの前後方向に0.35m離れた位置
target_y = blue_box_y

# ロボットがこの位置に到達するまで前後に移動（左右は0）
# まず、目標までの距離を計算
current_x, current_y = get_position()
distance_to_target = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)

# 移動のためのループ（最大120秒まで）
max_steps = 300
for step in range(max_steps):
    current_x, current_y = get_position()
    distance_to_target = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
    
    if distance_to_target < 0.1:  # 0.1m以内なら目標に到達
        break
        
    # 前後に移動（左右は0、旋回は0）
    # 前後の速度を距離に応じて調整（最大1.0 m/s）
    vx = min(1.0, 0.5 * distance_to_target / 0.5)  # 0.5 m/s で移動
    walk(vx, 0.0, 0.0, duration=0.1)

# 目標に到達後、青い箱の方向（+y 方向）を向く
# 青い箱の中心は (2.0, 2.0)、ロボットは (target_x, target_y) にいる
# つまり、青い箱の中心からロボットの位置を計算して、その方向を向く
target_dir_x = blue_box_x - current_x
target_dir_y = blue_box_y - current_y
target_angle = math.degrees(math.atan2(target_dir_y, target_dir_x))

# 現在の向きを取得
current_yaw = get_yaw()

# ターゲット角度に近づくまで左回り（負の角速度）で旋回
# 目標は90度（+y 方向）を向く → つまり、y軸方向を向く
# 90度に近づくまで回転
target_yaw = 90.0
for step in range(200):  # 最大20秒
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
    
# 最終的に止まる
stop(0.5)
