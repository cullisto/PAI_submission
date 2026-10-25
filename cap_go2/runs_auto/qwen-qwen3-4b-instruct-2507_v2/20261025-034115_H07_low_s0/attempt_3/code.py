# 青い箱の中心位置を取得
blue_box_x, blue_box_y = get_object_position("blue_box")

# ロボットの現在位置と向きを取得
x, y = get_position()
current_yaw = get_yaw()

# 安全距離：ロボットの前後方向に0.35m（胴体の長さの半分）を確保
safe_distance = 0.35

# 目標までの距離を計算（初期値）
target_distance = math.sqrt((blue_box_x - x)**2 + (blue_box_y - y)**2)

# 移動のための最大ステップ数（120秒以内に達成、0.1秒/ステップ）
max_steps = 1200
step_duration = 0.1

# 前後方向の移動速度（0.5 m/s）と横歩き速度（0.3 m/s）を設定
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
    
    # 安全距離に達していない場合、前後方向に移動
    if dist > safe_distance:
        # 前後方向への距離成分（ロボットの向きに沿った距離）
        forward_component = dx * cos_yaw + dy * sin_yaw
        
        # 前後方向に移動（前が正）
        if forward_component > 0:
            walk(0.5, 0.0, 0.0, duration=step_duration)
        else:
            # 後退（前進方向が逆の場合）
            walk(-0.3, 0.0, 0.0, duration=step_duration)
    else:
        # 安全距離内 → 横歩きで調整（左右方向にずれを補正）
        # 左右方向のずれを計算（ロボットの向きに垂直な方向）
        lateral_component = -dx * sin_yaw + dy * cos_yaw
        
        # 横歩きの速度を距離に応じて調整（距離が小さいほど遅く）
        lateral_speed = 0.3 * (1 - dist / safe_distance)
        
        # ずれがある場合にのみ横歩き
        if abs(lateral_component) > 0.05:
            if lateral_component > 0:
                walk(0.0, lateral_speed, 0.0, duration=step_duration)
            else:
                walk(0.0, -lateral_speed, 0.0, duration=step_duration)
    
    # 動作の確認（ログに残す、10ステップごとに表示）
    if step % 10 == 0:
        print(f"Step {step}: pos={x:.2f},{y:.2f}, yaw={current_yaw:.1f} deg, dist={dist:.2f}m")
    
    # 安全距離に達した場合、移動を終了
    if dist <= safe_distance:
        break

# 到達後、5秒間静止
stop(5.0)
