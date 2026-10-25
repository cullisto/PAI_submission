```python
# 赤い箱と青い箱の中心座標を取得し、そのちょうど中間の地点を目標に設定
red_center = get_object_position("red_box")
blue_center = get_object_position("blue_box")

# 中間点の座標を計算（x方向とy方向の平均）
target_x = (red_center[0] + blue_center[0]) / 2.0
target_y = (red_center[1] + blue_center[1]) / 2.0

# ロボットの現在の位置と向きを記録
x0, y0 = get_position()
current_yaw = get_yaw()

# ロボットの大きさを考慮して、物体との距離を安全に保つための安全距離を設定
# 軸方向の安全距離（胴体の半径：前後0.35m、左右0.15m）
safe_distance = 0.35  # 前後方向の安全距離（物体に近づかないように）

# ターゲットまでの距離を計算
target_distance = math.sqrt((target_x - x0)**2 + (target_y - y0)**2)

# 目標地点まで移動するまで、安全に進むようにする（物体にぶつからないようにチェック）
for step in range(300):  # 最大30秒以内に達成
    x, y = get_position()
    current_yaw_deg = get_yaw()
    
    # 目標地点へのベクトル
    dx = target_x - x
    dy = target_y - y
    
    # 現在の向き（ラジアン）に沿った進捗量
    progress = dx * math.cos(math.radians(current_yaw_deg)) + dy * math.sin(math.radians(current_yaw_deg))
    
    # 進捗が目標距離以上なら終了
    if progress >= target_distance:
        break
        
    # 現在の位置から物体までの距離をチェック（特に赤い箱と青い箱に近づかないように）
    # 各物体に近づいていないかを確認（安全距離を考慮）
    objects = get_objects()
    safe = True
    
    for obj in objects:
        obj_x, obj_y = obj["x"], obj["y"]
        obj_size_x, obj_size_y = obj["size_x"], obj["size_y"]
        
        # ロボットの中心から物体の中心までの距離
        dist_to_obj = math.sqrt((x - obj_x)**2 + (y - obj_y)**2)
        
        # ロボットの向きに応じて、物体に近づくかどうかの安全距離を計算
        # 前後方向（x軸）に近づく場合：安全距離は 0.35m（胴体の長さの半分）
        # 左右方向（y軸）に近づく場合：安全距離は 0.15m
        # ただし、物体の大きさを考慮して、物体の端までに近づかないようにする
        if dist_to_obj < (safe_distance + obj_size_x / 2.0):
            # 物体に近づいている → 前進を中止し、向きを調整
            safe = False
            break
    
    # 安全距離に違反している場合は、前進を中止して向きを調整
    if not safe:
        # 現在の位置から目標地点へのベクトルをもとに、向きを調整
        target_dir = math.atan2(target_y - y, target_x - x)
        target_yaw_deg = math.degrees(target_dir)
        
        # 目標向きに近づくように旋回（左回りが正）
        yaw_error = target_yaw_deg - current_yaw_deg
        # エラーを -180〜180 に収める
        yaw_error = (yaw_error + 180.0) % 360.0 - 180.0
        
        # 旋回速度を調整（小さめの角速度で回転）
        rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_error)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
            
        walk(0.0, 0.0, rate, duration=0.1)
        continue
    
    # 安全な状態であれば、前進
    walk(0.5, 0.0, 0.0, duration=0.1)

# 到達後、5秒間停止
stop(5.0)
```