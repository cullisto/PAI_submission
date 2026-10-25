# 赤い箱と青い箱の中心座標を取得し、そのちょうど中間の地点を目標に設定
red_center = get_object_position("red_box")
blue_center = get_object_position("blue_box")

# 中間点の座標を計算（x方向とy方向の平均）
target_x = (red_center[0] + blue_center[0]) / 2.0
target_y = (red_center[1] + blue_center[1]) / 2.0

# 現在の位置と目標までの距離を計算
x0, y0 = get_position()
target_distance = math.sqrt((target_x - x0)**2 + (target_y - y0)**2)

# 目標地点まで移動するまで前進する（向きを調整しながら）
for _ in range(300):  # 最大30秒以内に達成
    x, y = get_position()
    # 現在の向きから目標地点へのベクトルを計算
    dx = target_x - x
    dy = target_y - y
    # 位置の進捗量（現在の向きに沿った距離）
    progress = dx * math.cos(math.radians(get_yaw())) + dy * math.sin(math.radians(get_yaw()))
    
    # 進捗が目標距離以上になったら終了
    if progress >= target_distance:
        break
        
    # 前進速度を0.5で設定（安全な速度で進む）
    walk(0.5, 0.0, 0.0, duration=0.1)

# 到達後、5秒間停止
stop(5.0)
