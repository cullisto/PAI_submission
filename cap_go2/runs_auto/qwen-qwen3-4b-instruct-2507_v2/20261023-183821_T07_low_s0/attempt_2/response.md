```python
# 開始時の位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 1メートル後ろに下がる（後ろが負方向なので vx は負）
# 目標位置は (0.0, 0.0) から後ろに1mなので (-1.0, 0.0)
target_x, target_y = -1.0, 0.0

# 現在の向きに沿って距離を計算し、1m後退するまで後進
for _ in range(300):  # 最大30秒
    x, y = get_position()
    # ロボットの向き（yaw）に沿った距離を計算
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.sqrt(dx*dx + dy*dy)
    
    # 向きに沿った進み方を計算（現在の向きに沿って目標点への距離）
    progress = dx * math.cos(math.radians(yaw0)) + dy * math.sin(math.radians(yaw0))
    if progress <= -1.0:
        break
    
    # 進む速度を調整（後退速度を0.5に保ちつつ、安定して進む）
    walk(-0.5, 0.0, 0.0, duration=0.1)

# その後、右に45度回る（右回りなので yaw_rate は負）
target_yaw = yaw0 + 45.0
for _ in range(200):  # 最大20秒
    current_yaw = get_yaw()
    # より正確に角度誤差を計算（-180〜180の範囲で）
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    # 角度誤差に基づいて旋回速度を計算（最大1.0rad/s）
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, -rate, duration=0.1)

# 最終的に停止
stop(0.5)
```