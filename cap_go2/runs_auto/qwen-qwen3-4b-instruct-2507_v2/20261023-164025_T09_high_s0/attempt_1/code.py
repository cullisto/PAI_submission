# 左回りに円を描くように一周する（半径 1.0 m）
# 初期位置と向きを確認
x, y = get_position()
initial_yaw = get_yaw()

# 円の中心を初期位置に設定（原点を中心に円を描く）
center_x, center_y = x, y
radius = 1.0
total_angle = 360.0  # 一周
angle_step = 10.0    # 10度ごとに角度を進める
duration_per_step = 0.5  # 各ステップで0.5秒

# 一周するためのループ（角度を0〜360度まで進める）
for angle in range(0, total_angle + 1, angle_step):
    # 目標位置を円の周上に設定（左回り）
    target_x = center_x + radius * math.cos(math.radians(angle))
    target_y = center_y + radius * math.sin(math.radians(angle))
    
    # 今の向きに合わせて旋回して、目標方向を向く（円を描くための向き調整）
    current_yaw = get_yaw()
    target_yaw = current_yaw + angle_step  # 左回りに進む
    target_yaw = target_yaw % 360.0
    
    # 旋回して目標の向きにする
    turn(target_yaw - current_yaw)
    
    # 目標位置に移動（距離を0.5mで進む）
    move_forward(0.5)

# 最後に元の位置付近に戻る（1m以内に収める）
x, y = get_position()
target_x, target_y = 0.0, 0.0
distance = math.hypot(x - target_x, y - target_y)
if distance > 0.3:
    # 直進で元の場所に近づく
    move_to(target_x, target_y, tolerance=0.3)
    
stop(1.0)
