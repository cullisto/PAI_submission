```python
# 赤い箱の中心位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 赤い箱までの距離を計算
target_distance = math.sqrt((red_box_x - x0) ** 2 + (red_box_y - y0) ** 2)

# ロボットの向きを赤い箱に向ける（旋回を確実に実行）
for _ in range(300):  # 最大 30 秒
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    # ターゲットの方向（atan2で角度を計算）
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 向きの誤差を -180〜180 度で計算
    yaw_err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    
    # 誤差が小さい場合（±3度以内）に停止
    if abs(yaw_err) < 3.0:
        break
    
    # 角速度を誤差に比例して調整（速すぎないよう制限）
    rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    
    # 旋回を0.1秒単位で実行
    walk(0.0, 0.0, rate, duration=0.1)

# 向きが正しい状態で、安全な距離を考慮して前進（物体にぶつからないように）
# ロボットの前後方向の安全距離は 0.35m（胴体の半分）
safe_distance = 0.35
max_approach = target_distance - safe_distance

# 前進を安全に実行（最大30秒で、安全距離内に達するまで）
for _ in range(300):  # 最大 30 秒
    current_x, current_y = get_position()
    current_yaw = get_yaw()
    
    dx = red_box_x - current_x
    dy = red_box_y - current_y
    dist = math.sqrt(dx**2 + dy**2)
    
    # 安全距離を超えていないか確認
    if dist <= safe_distance:
        break
    
    # 前進速度を距離に応じてスケーリング（最大1.0m/s）
    vx = min(1.0, max(-0.5, 0.5 * (max_approach / dist)))
    
    # 前進を0.1秒単位で実行
    walk(vx, 0.0, 0.0, duration=0.1)

# 最終的に赤い箱に到達したことを確認し、止まる
stop(1.0)
```