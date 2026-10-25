# 青い箱の中心位置を取得
blue_box_x, blue_box_y = get_object_position("blue_box")

# ロボットの現在位置と向きを取得
x, y = get_position()
current_yaw = get_yaw()

# 目標点（青い箱の中心）までの距離を計算
target_distance = math.sqrt((blue_box_x - x)**2 + (blue_box_y - y)**2)

# 安全距離：ロボットの前後方向に0.35m、左右に0.15mの距離を確保
safe_distance = 0.35  # 前後方向にロボットの中心が箱に近づかないように

# 移動のための最大ステップ数（120秒以内に達成）
max_steps = 600
step_duration = 0.1

# 前後方向に移動する速度を0.5 m/s、横歩きは0.3 m/sに設定
for step in range(max_steps):
    # 現在の位置を取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの向きに沿った前後方向の距離成分を計算
    cos_yaw = math.cos(math.radians(current_yaw))
    sin_yaw = math.sin(math.radians(current_yaw))
    
    # 目標点へのベクトル
    dx = blue_box_x - x
    dy = blue_box_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    # 安全距離に達していない場合、移動
    if dist > safe_distance:
        # 前後方向への移動量（ロボットの向きに沿った距離）
        forward_component = dx * cos_yaw + dy * sin_yaw
        
        # 前後方向に移動（前が正）
        if forward_component > 0:
            # 前進
            walk(0.5, 0.0, 0.0, duration=step_duration)
        else:
            # 後退（必要に応じて）
            walk(-0.3, 0.0, 0.0, duration=step_duration)
    else:
        # 安全距離内に達した → 横歩きで調整（左右方向にずれを補正）
        # 左右方向のずれを計算（ロボットの向きに垂直な方向）
        lateral_component = -dx * sin_yaw + dy * cos_yaw
        
        # 横歩きの速度を距離に応じて調整（距離が小さいほど遅く）
        lateral_speed = 0.3 * (1 - dist / safe_distance)
        if abs(lateral_component) > 0.1:
            # 左右にずれている場合
            if lateral_component > 0:
                walk(0.0, 0.3, 0.0, duration=step_duration)
            else:
                walk(0.0, -0.3, 0.0, duration=step_duration)
    
    # 動作の確認（ログに残す）
    if step % 10 == 0:
        print(f"Step {step}: pos={x:.2f},{y:.2f}, yaw={current_yaw:.1f} deg, dist={dist:.2f}m")

# 到達後、5秒間静止
stop(5.0)
