# 開始時の位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標位置は (-1.0, 0.0) に到達する（1m後ろ）
target_x, target_y = -1.0, 0.0

# 現在の位置と向きをもとに、目標点に近づくまで後退する
for _ in range(500):  # 最大50秒（安全な上限）
    x, y = get_position()
    # 現在の向きに沿った目標点への距離を計算
    dx = target_x - x
    dy = target_y - y
    distance = math.sqrt(dx*dx + dy*dy)
    
    # 進む方向（現在の向きに沿ったベクトル）の距離を計算
    progress = dx * math.cos(math.radians(yaw0)) + dy * math.sin(math.radians(yaw0))
    
    # 距離が0.4m未満なら終了（誤差許容範囲）
    if distance <= 0.4:
        break
        
    # 進む速度を0.5で後退（後ろが負方向）
    walk(-0.5, 0.0, 0.0, duration=0.1)

# その後、右に45度回る（右回りなので yaw_rate は負）
target_yaw = yaw0 + 45.0
for _ in range(200):  # 最大20秒
    current_yaw = get_yaw()
    # 角度誤差を -180～180 で正確に計算
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    # 旋回速度を誤差に比例して調整（最大±1.0 rad/s）
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, -rate, duration=0.1)

# 最終的に停止
stop(0.5)
