# 青い箱に寄ってから、緑の箱まで行ってる
# 原因: ロボットが青い箱に近づけなかった（距離が0.5m未満に到達しなかった）→ 適切な移動戦略が欠けていた
# 修正点:
# 1. 青い箱に向かって正確に移動するように、常にロボットの向きを調整しながら進む
# 2. 青い箱に近づくまで、正確に目標に向かって移動（向きを調整しながら）
# 3. 青い箱に到達した後、緑の箱へ向かって移動する

# 青い箱の中心位置を取得
blue_box_pos = get_object_position("blue_box")
blue_x, blue_y = blue_box_pos

# 緑の箱の中心位置を取得
green_box_pos = get_object_position("green_box")
green_x, green_y = green_box_pos

# 初期位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 青い箱に近づくまで（最大300回、約30秒）
for _ in range(300):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの向きに沿った青い箱までの距離（前方方向）
    dx = blue_x - x
    dy = blue_y - y
    distance_to_blue = math.sqrt(dx*dx + dy*dy)
    
    # ロボットの向きに沿った距離（前方方向）
    forward_dist = dx * math.cos(math.radians(current_yaw)) + dy * math.sin(math.radians(current_yaw))
    
    # 青い箱に近づく（距離が0.5m未満になるまで）
    if distance_to_blue <= 0.5:
        break
        
    # ロボットの向きを青い箱に向かって調整（目標方向を計算）
    target_yaw = math.degrees(math.atan2(dy, dx))
    # より安定に回転させるために、目標と現在の向きの差を計算
    yaw_diff = target_yaw - current_yaw
    # -180 ~ 180 の範囲で調整
    if yaw_diff > 180:
        yaw_diff -= 360
    elif yaw_diff < -180:
        yaw_diff += 360
        
    # 旋回速度を差に応じて調整（-1.0 ~ 1.0）
    rate = max(-1.0, min(1.0, 0.5 * yaw_diff / 10.0))
    if abs(rate) < 0.1:
        rate = 0.1 * math.copysign(1, rate)
    
    # 前後方向に移動（速度0.5m/s）
    walk(0.5, 0.0, rate, duration=0.1)

# 青い箱に近づいたら、緑の箱へ向かう
# 緑の箱までの移動
for _ in range(300):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 緑の箱までの距離（ロボットの向きに沿った距離）
    dx = green_x - x
    dy = green_y - y
    distance_to_green = math.sqrt(dx*dx + dy*dy)
    
    # ロボットの向きに沿った距離
    forward_dist_to_green = dx * math.cos(math.radians(current_yaw)) + dy * math.sin(math.radians(current_yaw))
    
    # 緑の箱に近づく（距離が0.5m未満になるまで）
    if distance_to_green <= 0.5:
        break
        
    # 緑の箱に向かって向きを調整
    target_yaw_green = math.degrees(math.atan2(dy, dx))
    yaw_diff_green = target_yaw_green - current_yaw
    if yaw_diff_green > 180:
        yaw_diff_green -= 360
    elif yaw_diff_green < -180:
        yaw_diff_green += 360
        
    rate_green = max(-1.0, min(1.0, 0.5 * yaw_diff_green / 10.0))
    if abs(rate_green) < 0.1:
        rate_green = 0.1 * math.copysign(1, rate_green)
    
    # 前後方向に移動
    walk(0.5, 0.0, rate_green, duration=0.1)

# 最終的に止まる
stop(1.0)
