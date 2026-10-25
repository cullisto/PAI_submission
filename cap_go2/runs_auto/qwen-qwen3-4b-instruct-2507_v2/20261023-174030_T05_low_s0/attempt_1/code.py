# 1辺1メートルの正方形を描くために、4つの辺を前進・右回りで移動する
# 各辺の長さは1m、ロボットの向きを90度ずつ変更する
# 軌道は、開始位置(0,0)から、x軸方向に1m進み、右に90度回り、y軸方向に1m進み、さらに右に90度回り、x軸方向に1m進み、右に90度回り、y軸方向に1m進み、右に90度回り、元の位置に戻る

# 初期位置と向きを取得
x, y = get_position()
yaw = get_yaw()

# 各移動の目標位置と向きを計算
target_positions = [
    (1.0, 0.0),   # 右に1m
    (1.0, 1.0),   # 前に1m
    (0.0, 1.0),   # 左に1m
    (0.0, 0.0)    # 後に1m（元の位置に戻る）
]

# 各移動の目標方向（0度で右、90度で前、180度で左、270度で後）
target_yaws = [0.0, 90.0, 180.0, 270.0]

# 4つの辺を描く
for i in range(4):
    target_x, target_y = target_positions[i]
    target_yaw = target_yaws[i]
    
    # 現在の位置と向きから、目標位置まで移動するまでの距離を計算
    # ロボットの向きに合わせて移動距離を計算
    dx = target_x - x
    dy = target_y - y
    distance = math.hypot(dx, dy)
    
    # 移動距離が0ならスキップ（元の場所にいる場合）
    if distance < 0.01:
        x, y = target_positions[i]
        continue
        
    # 目標の向きに到達するまで旋回（90度ずつ）
    current_yaw = get_yaw()
    target_yaw_rad = math.radians(target_yaw)
    current_yaw_rad = math.radians(current_yaw)
    
    # 旋回の誤差を計算（目標と現在の向きの差）
    angle_diff = (target_yaw_rad - current_yaw_rad) % (2 * math.pi)
    if angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    
    # 旋回の角速度を調整（最大1.0 rad/s）
    if abs(angle_diff) < 0.1:
        yaw_rate = 0.0
    else:
        yaw_rate = max(-1.0, min(1.0, 1.0 * angle_diff / 0.5))
    
    # 旋回を実行（最大10秒まで）
    for _ in range(200):
        current_yaw = get_yaw()
        current_yaw_rad = math.radians(current_yaw)
        angle_diff = (target_yaw_rad - current_yaw_rad) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        if abs(angle_diff) < 0.1:
            break
        walk(0.0, 0.0, yaw_rate, duration=0.1)
    
    # 移動（1mの距離を前進または左右に移動）
    # 速度は0.5 m/sで移動（1mは2秒で達成）
    for _ in range(200):
        x, y = get_position()
        dist = math.hypot(x - target_x, y - target_y)
        if dist < 0.01:
            break
        walk(0.5, 0.0, 0.0, duration=0.1)  # 前後方向に移動（x方向）
    
    # 現在の位置を更新
    x, y = get_position()

# 最後に元の位置に戻る（0,0）
# 0.5 m/sで移動（距離が0.5mなら1秒）
for _ in range(200):
    x, y = get_position()
    dist = math.hypot(x, y)
    if dist < 0.01:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)

# 最終的に止まる
stop(1.0)
