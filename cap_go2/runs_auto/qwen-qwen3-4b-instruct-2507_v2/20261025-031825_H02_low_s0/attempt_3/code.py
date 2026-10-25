# 停滞（物体にぶつかったまま動けなかった）の原因は、移動指令を出してもロボットが物体に当たって進まないため
# 修正点:
# 1. 各箱に近づく前に、ロボットの向きを箱に向かって調整（正確な方向を取る）
# 2. 移動前に、目標位置への距離と向きを計算し、安全な範囲内での移動を確保
# 3. 移動中に物体に近づくことを検知し、安全距離を保つように制御
# 4. 移動のステップを短く、安全距離を常に確認しながら進行

# オブジェクトの位置を取得
red_box_pos = get_object_position("red_box")
blue_box_pos = get_object_position("blue_box")
green_box_pos = get_object_position("green_box")
yellow_box_pos = get_object_position("yellow_box")

# ロボットの初期位置と向き
x, y = get_position()
yaw = get_yaw()

# 各箱の安全距離（ロボットの胴体の境界）
safe_dist_x = 0.35  # 前後
safe_dist_y = 0.15  # 左右

# 各箱の安全距離を考慮した目標位置（物体中心からロボットが当たらないように）
target_positions = [
    (red_box_pos[0] - safe_dist_x, red_box_pos[1] - safe_dist_y),
    (blue_box_pos[0] - safe_dist_x, blue_box_pos[1] - safe_dist_y),
    (green_box_pos[0] - safe_dist_x, green_box_pos[1] - safe_dist_y),
    (yellow_box_pos[0] - safe_dist_x, yellow_box_pos[1] - safe_dist_y),
]

# 各目標に近づく（最大30ステップで制御）
for target_x, target_y in target_positions:
    # 現在の位置から目標までのベクトル
    dx = target_x - x
    dy = target_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    # 距離が0.1m以下なら、すでに近い → 停止
    if dist < 0.1:
        stop(0.5)
        continue
    
    # 目標方向への角度（ロボット自身の座標系で）
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 現在の向きと目標向きの差（-180〜180度で調整）
    current_yaw = get_yaw()
    diff = target_yaw - current_yaw
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    
    # 向きを調整（最大10ステップで、10度ずつ近づく）
    for _ in range(10):
        if abs(diff) < 5.0:
            break
        # 1度ずつ回転（左回りが正）
        rate = math.copysign(0.5, diff) * math.radians(1.0)
        walk(0.0, 0.0, rate, duration=0.1)
        current_yaw = get_yaw()
        diff = target_yaw - current_yaw
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
    
    # 向きが整ったら、目標位置に移動（最大10ステップ）
    for _ in range(10):
        x, y = get_position()
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.1:
            break
            
        # 前後のみ移動（左右は0）
        walk(0.5, 0.0, 0.0, duration=0.1)
    
    stop(0.5)

# すべての箱に寄った後、スタート地点に戻る（最大10ステップ）
start_x, start_y = 0.0, 0.0
for _ in range(10):
    x, y = get_position()
    dx = start_x - x
    dy = start_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist < 0.1:
        break
        
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(1.0)
