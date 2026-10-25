# 青い箱に寄ってから、緑の箱まで行ってる
# 1. 青い箱の位置を取得し、ロボットがその箱に近づくまで前進・旋回
# 2. 青い箱に到達したら、緑の箱へ向かって移動

# 青い箱の中心位置を取得
blue_box_pos = get_object_position("blue_box")
blue_x, blue_y = blue_box_pos

# 緑の箱の中心位置を取得
green_box_pos = get_object_position("green_box")
green_x, green_y = green_box_pos

# 初期位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 青い箱に近づくまでのループ（最大60秒）
for _ in range(300):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの中心から青い箱までの距離を計算（ロボットの前後方向で）
    # ロボットの向きに沿った距離（前方方向）を計算
    forward_dist = (x - blue_x) * math.cos(math.radians(current_yaw)) + (y - blue_y) * math.sin(math.radians(current_yaw))
    
    # 距離が0.5m未満なら、青い箱に近づいていると判断
    if forward_dist <= 0.5:
        break
        
    # ロボットが青い箱に向かって進むようにする
    # 前後方向の速度を0.5に設定、左右は0
    walk(0.5, 0.0, 0.0, duration=0.1)

# 青い箱に到達したら、緑の箱へ向かう
# 緑の箱までの移動
for _ in range(300):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 緑の箱までの距離（ロボットの向きに沿った距離）
    forward_dist_to_green = (x - green_x) * math.cos(math.radians(current_yaw)) + (y - green_y) * math.sin(math.radians(current_yaw))
    
    # 距離が0.5m未満なら、緑の箱に近づいていると判断
    if forward_dist_to_green <= 0.5:
        break
        
    # 緑の箱に向かって進む（前後方向に0.5m/s）
    walk(0.5, 0.0, 0.0, duration=0.1)

# 最終的に止まる
stop(1.0)
