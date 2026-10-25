# 赤い箱と青い箱の中心座標を取得し、そのちょうど中間の地点を目標に設定
red_center = get_object_position("red_box")  # (3.0, 0.0)
blue_center = get_object_position("blue_box")  # (2.0, 2.0)

# 中間点の座標を計算（x方向とy方向の平均）
target_x = (red_center[0] + blue_center[0]) / 2.0
target_y = (red_center[1] + blue_center[1]) / 2.0

# 目標点を確認（赤と青の中間：(2.5, 1.0)）
print(f"目標点: ({target_x:.1f}, {target_y:.1f})")

# ロボットの初期位置と向きを取得
x0, y0 = get_position()
current_yaw = get_yaw()

# 安全距離：ロボットの胴体サイズを考慮（前後 0.35m, 左右 0.15m）
safe_distance_x = 0.35  # 前後方向
safe_distance_y = 0.15  # 左右方向

# ターゲットまでの距離を計算
target_distance = math.sqrt((target_x - x0)**2 + (target_y - y0)**2)

# 安全に移動するまで、ステップごとに進む（最大30秒以内）
for step in range(300):
    x, y = get_position()
    current_yaw_deg = get_yaw()
    
    # 目標地点へのベクトル
    dx = target_x - x
    dy = target_y - y
    
    # 現在の向きに沿った進捗量（距離の進捗）
    progress = dx * math.cos(math.radians(current_yaw_deg)) + dy * math.sin(math.radians(current_yaw_deg))
    
    # 進捗が目標距離の90%以上になったら終了（安全に到達）
    if progress >= 0.9 * target_distance:
        break
        
    # 各物体（箱）に近づいていないかをチェック（安全距離を考慮）
    objects = get_objects()
    safe = True
    
    for obj in objects:
        obj_x, obj_y = obj["x"], obj["y"]
        obj_size_x, obj_size_y = obj["size_x"], obj["size_y"]
        
        # ロボットの中心から物体の中心までの距離
        dist_to_obj = math.sqrt((x - obj_x)**2 + (y - obj_y)**2)
        
        # 物体の端までの距離（安全距離）
        min_dist = safe_distance_x if abs(dx) > abs(dy) else safe_distance_y
        min_dist = min(min_dist, 0.35)  # 最大0.35m
        
        # 物体に近づいているかチェック（物体の端までに近づかないように）
        if dist_to_obj < (min_dist + obj_size_x / 2.0):
            safe = False
            break
    
    # 安全距離に違反している場合、向きを調整
    if not safe:
        # 目標地点への方向を計算
        target_dir_rad = math.atan2(target_y - y, target_x - x)
        target_yaw_deg = math.degrees(target_dir_rad)
        
        # 現在の向きと目標向きの差を計算（-180〜180度）
        yaw_error = target_yaw_deg - current_yaw_deg
        yaw_error = (yaw_error + 180.0) % 360.0 - 180.0
        
        # 旋回速度を調整（小さめで安全に回転）
        rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_error)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
            
        walk(0.0, 0.0, rate, duration=0.1)
        continue
    
    # 安全な状態なら、前進（0.5m/s）
    walk(0.5, 0.0, 0.0, duration=0.1)

# 到達後、5秒間停止（タスク完了を確認）
stop(5.0)
