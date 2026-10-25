# 一番近い箱まで行って、その箱に近づくまで移動する
# 各箱の中心位置を取得し、ロボットの現在位置から距離を計算して最も近い箱を選び、その方向に移動する
positions = [
    ("red_box", (3.0, 0.0)),
    ("blue_box", (2.0, 2.0)),
    ("green_box", (0.5, -2.5)),
    ("yellow_box", (-2.0, 1.0))
]

# 現在のロボットの位置と向きを取得
x0, y0 = get_position()
current_yaw = get_yaw()

# 最も近い箱までの距離を計算し、その箱の位置を記録
min_distance = float('inf')
target_x, target_y = 0.0, 0.0

for name, (x, y) in positions:
    dist = distance_to(x, y)
    if dist < min_distance:
        min_distance = dist
        target_x, target_y = x, y

# ターゲットまでの距離が0より大きい場合にのみ移動（最初に近い箱に近づく）
if min_distance > 0.0:
    # 目標地点までのベクトルを計算
    dx = target_x - x0
    dy = target_y - y0
    # ロボットの現在の向きを考慮して、目標方向に向けた角度を計算（atan2で角度を求める）
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 現在の向きと目標向きの差を計算（-180〜180度の範囲で）
    yaw_diff = target_yaw - current_yaw
    # 角度を -180〜180 に調整
    while yaw_diff > 180:
        yaw_diff -= 360
    while yaw_diff < -180:
        yaw_diff += 360
    
    # 目標までの距離を確保するため、目標点に近づくまで移動
    # 1秒間に最大0.5mの速度で移動（前後速度）
    max_speed = 0.5
    target_distance = math.sqrt(dx*dx + dy*dy)
    
    # 最大120秒以内に到達するように、ステップで移動
    for _ in range(1000):  # 最大1000ステップ（約20秒）
        x, y = get_position()
        current_dist = math.sqrt((x - target_x)**2 + (y - target_y)**2)
        
        # 0.1m未満に近づいたら停止
        if current_dist < 0.1:
            break
            
        # 旋回が必要かを判断（向きがずれている場合）
        if abs(yaw_diff) > 5.0:
            # 旋回速度を調整（左回りが正）
            rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_diff)))
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=0.1)
            current_yaw = get_yaw()
            yaw_diff = target_yaw - current_yaw
            while yaw_diff > 180:
                yaw_diff -= 360
            while yaw_diff < -180:
                yaw_diff += 360
        else:
            # 向きが合っていれば、前進
            walk(max_speed, 0.0, 0.0, duration=0.1)
else:
    # すべての箱が0距離の場合（理論的にはありえないが、安全策）
    stop(1.0)

# 到達後、1秒間停止
stop(1.0)
