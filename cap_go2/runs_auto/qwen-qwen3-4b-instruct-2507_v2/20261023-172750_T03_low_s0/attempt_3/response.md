```python
# 赤い箱の中心位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# 初期位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 赤い箱までの距離を計算
target_distance = math.sqrt((red_box_x - x0) ** 2 + (red_box_y - y0) ** 2)

# 旋回：赤い箱の方向に向けられるまでゆっくり回転（最大30秒）
for _ in range(300):
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    # ターゲット方向（atan2で角度を計算）
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 向きの誤差（-180～180度）
    yaw_err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    
    # 誤差が小さい場合（±3度以内）に終了
    if abs(yaw_err) < 3.0:
        break
        
    # 角速度を誤差に比例して調整（急な回転を避ける）
    rate = max(-1.0, min(1.0, 0.8 * math.radians(yaw_err)))
    if abs(rate) < 0.1:
        rate = math.copysign(0.1, rate)
        
    # 0.1秒単位で旋回（過剰な移動を防ぐ）
    walk(0.0, 0.0, rate, duration=0.1)

# 前進：安全な距離（0.35m）を考慮して、赤い箱に近づく
safe_distance = 0.35
max_approach = target_distance - safe_distance

# 前進ループ（最大30秒、安全距離内に達するまで）
for _ in range(300):
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    dist = math.sqrt(dx**2 + dy**2)
    
    # 安全距離を超えていないか確認
    if dist <= safe_distance:
        break
        
    # 前進速度を距離に応じて調整（最大1.0m/s）
    vx = min(1.0, max(-0.5, 0.6 * (max_approach / dist)))
    
    # 前進を0.1秒単位で実行（移動を確実に進める）
    walk(vx, 0.0, 0.0, duration=0.1)

# 最終的に赤い箱に到達したことを確認し、止まる
stop(1.0)
```