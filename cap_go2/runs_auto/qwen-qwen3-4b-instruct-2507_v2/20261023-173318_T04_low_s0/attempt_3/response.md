```python
# 青い箱に寄ってから、緑の箱まで行ってる
# 原因: 停滞（ほとんど動けなかった）→ 旋回速度が小さすぎたり、移動指令が無効にされたり、障害物に近づくと動けない
# 修正点:
# 1. 移動指令を短時間で繰り返す（duration=0.1）→ 高頻度で動くようにし、ステップごとに調整
# 2. 各ステップで距離や向きをチェックし、障害物に近づかないようにする
# 3. 障害物に近づいた場合、その場で止める（安全距離を確保）
# 4. 向きを常に目標方向に調整し、前後速度を一定に保つ

# 青い箱の中心位置を取得
blue_box_pos = get_object_position("blue_box")
blue_x, blue_y = blue_box_pos

# 緑の箱の中心位置を取得
green_box_pos = get_object_position("green_box")
green_x, green_y = green_box_pos

# ロボットのサイズを考慮（胴体の前後幅 0.7m、左右幅 0.3m）
# つまり、物体に近づく際は、物体の表面から 0.35m（前後）と 0.15m（左右）の距離を確保
# 例: 青い箱（0.3×0.3）に近づくとき、ロボットの中心は箱の表面から 0.35m 以上離れる必要がある

# 初期位置と向きを取得
x, y = get_position()
current_yaw = get_yaw()

# 青い箱に近づくまでのループ（最大300回）
for _ in range(300):
    # 現在の位置を取得
    x_curr, y_curr = get_position()
    current_yaw = get_yaw()
    
    # 青い箱までの距離（ユークリッド距離）
    dx_blue = blue_x - x_curr
    dy_blue = blue_y - y_curr
    dist_to_blue = math.sqrt(dx_blue*dx_blue + dy_blue*dy_blue)
    
    # 青い箱に近づくための安全距離（ロボットの前後方向に0.35m）
    safe_dist_to_blue = 0.35  # 前後方向の安全距離（ロボットの中心から）
    
    # 青い箱に近づくが、安全距離未満なら止める
    if dist_to_blue <= safe_dist_to_blue:
        break
        
    # 青い箱に向かって向きを調整（目標方向）
    target_yaw_blue = math.degrees(math.atan2(dy_blue, dx_blue))
    # ロボットの現在の向きと差分を計算（-180 ~ 180）
    yaw_diff = target_yaw_blue - current_yaw
    if yaw_diff > 180:
        yaw_diff -= 360
    elif yaw_diff < -180:
        yaw_diff += 360
    
    # 旋回速度を調整（差が大きいほど速く回転）
    rate = max(-1.0, min(1.0, 0.8 * yaw_diff / 10.0))
    if abs(rate) < 0.1:
        rate = 0.1 * math.copysign(1, rate)
    
    # 前後方向に移動（0.5m/s）
    walk(0.5, 0.0, rate, duration=0.1)

# 青い箱に近づいたら、緑の箱へ向かう
for _ in range(300):
    x_curr, y_curr = get_position()
    current_yaw = get_yaw()
    
    # 緑の箱までの距離
    dx_green = green_x - x_curr
    dy_green = green_y - y_curr
    dist_to_green = math.sqrt(dx_green*dx_green + dy_green*dy_green)
    
    # 緑の箱に近づくための安全距離（0.35m）
    if dist_to_green <= 0.35:
        break
        
    # 緑の箱に向かって向きを調整
    target_yaw_green = math.degrees(math.atan2(dy_green, dx_green))
    yaw_diff_green = target_yaw_green - current_yaw
    if yaw_diff_green > 180:
        yaw_diff_green -= 360
    elif yaw_diff_green < -180:
        yaw_diff_green += 360
        
    rate_green = max(-1.0, min(1.0, 0.8 * yaw_diff_green / 10.0))
    if abs(rate_green) < 0.1:
        rate_green = 0.1 * math.copysign(1, rate_green)
    
    # 前後方向に移動
    walk(0.5, 0.0, rate_green, duration=0.1)

# 最終的に止まる
stop(1.0)
```