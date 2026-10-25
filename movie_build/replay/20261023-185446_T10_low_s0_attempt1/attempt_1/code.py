# 壁にぶつからないように避けて、赤い箱まで行っていく
# 初期位置と向きを記録
x0, y0 = get_position()
current_yaw = get_yaw()

# 赤い箱と壁の位置を取得
red_box_pos = get_object_position("red_box")
wall_pos = get_object_position("wall")

# 赤い箱までの距離を計算（ロボットの中心から）
target_x, target_y = red_box_pos
target_distance = math.sqrt((target_x - x0)**2 + (target_y - y0)**2)

# 壁の位置と大きさを確認（壁は (2.0, 0.0) で 0.3×1.6）
wall_x, wall_y = wall_pos
wall_size_x, wall_size_y = 0.3, 1.6

# ロボットのサイズを考慮して、壁に近づかないように安全距離を設定
# ロボットの幅は左右 0.3 m、前後 0.7 m → 向いている方向に安全距離を確保
# 壁の中心 (2.0, 0.0) に近づく場合、ロボットの左右幅 0.3 m で左右に 0.15 m より近づかない

# 最大試行回数を設定（120秒以内に終了）
max_steps = 1000
for step in range(max_steps):
    # 現在の位置と向きを取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 赤い箱へのベクトルを計算（ロボットから見た方向）
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.sqrt(dx*dx + dy*dy)
    
    # 距離が小さければ、直進でゴールに近づく
    if distance_to_target < 0.2:
        walk(0.0, 0.0, 0.0, duration=0.1)
        break
    
    # 障害物（壁）との距離を計算（ロボットの中心から壁の中心までの距離）
    wall_center_x, wall_center_y = wall_pos
    wall_center_dx = wall_center_x - x
    wall_center_dy = wall_center_y - y
    wall_distance = math.sqrt(wall_center_dx**2 + wall_center_dy**2)
    
    # ロボットの左右幅（0.3m）と前後幅（0.7m）を考慮して、壁に近づかないようにする
    # 壁に近づくと、ロボットの中心が壁の範囲内に入ってしまう可能性がある
    # よって、壁に近づくと左右方向にずらす（壁に平行に進むように）
    
    # 壁が x 方向に伸びている（y 方向は 0.0 で、幅 1.6m）なので、y 方向にずらす
    # ロボットの中心が壁の y 方向範囲内に入らないようにする
    # 壁の y 方向範囲: (wall_y - wall_size_y/2, wall_y + wall_size_y/2) = (-0.8, 0.8)
    # ロボットの左右幅 0.3m → y 方向に 0.15m より近づかない
    robot_y_margin = 0.15
    wall_y_min = wall_y - wall_size_y / 2
    wall_y_max = wall_y + wall_size_y / 2
    
    # ロボットの y 位置が壁の y 範囲内にあるか確認
    if (y < wall_y_min + robot_y_margin) or (y > wall_y_max - robot_y_margin):
        # 壁の y 方向の範囲に近づいている → y 方向にずらす
        # 壁の中心 y に近づくように、y 方向に移動
        # 壁に近づく方向を y 方向に調整
        desired_y = wall_y
        if y < desired_y:
            vy = 0.3
        else:
            vy = -0.3
    else:
        # 壁に近づいていない → 直進
        vy = 0.0
    
    # 目標方向に向けた vx を計算（目標点へのベクトル方向）
    # より安全に進むために、目標点に向かって一定速度で進む
    # 前後速度を目標点方向に調整
    if distance_to_target > 0.1:
        # 目標点への単位ベクトル
        target_dir_x = dx / distance_to_target
        target_dir_y = dy / distance_to_target
        # 前後速度を目標方向に調整（x 方向に進む）
        vx = 0.5 * target_dir_x
        vy = 0.5 * target_dir_y
    else:
        vx = 0.0
        vy = 0.0
    
    # 速度を範囲内に収める
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # 旋回は不要（直進）
    yaw_rate = 0.0
    
    # 0.1秒間歩く
    walk(vx, vy, yaw_rate, duration=0.1)

# ゴールに到達したら、1秒間止まる
stop(1.0)
