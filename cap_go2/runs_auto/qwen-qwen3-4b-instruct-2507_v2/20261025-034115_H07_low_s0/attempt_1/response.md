```python
# 青い箱の中心位置を取得
blue_box_x, blue_box_y = get_object_position("blue_box")

# ロボットの現在位置と向きを取得
x, y = get_position()
current_yaw = get_yaw()

# 青い箱の中心に到達するまでの距離を計算（ロボットの中心から）
# ロボットの前後方向に移動するため、現在の向きに沿って距離を計算
# 軸変換: ロボットの向きに沿ったx方向とy方向の距離を計算
# 目標点への距離（ロボットの向きに沿った前後方向の距離）
distance_to_goal = math.sqrt((blue_box_x - x)**2 + (blue_box_y - y)**2)

# ロボットの大きさを考慮して、箱に近づく際の安全距離を確保
# 箱の大きさは 0.3m × 0.3m、ロボットの前後幅は 0.7m、左右幅は 0.3m
# 箱の中心に近づく際、ロボットの胴体が箱に当たらないようにする
# つまり、ロボットの中心が箱の境界まで近づくようにする
# 箱の中心からロボットの中心までの距離が、箱の大きさの半分（0.15m）より大きいようにする
# ただし、ロボットの前後方向に近づく場合、0.35mの安全距離が必要

# 安全距離の計算（前後方向）
safe_distance = 0.35  # 前後方向にロボットの中心が箱に近づかないようにする

# 安全距離を考慮して、目標までの距離を調整
target_distance = max(safe_distance, distance_to_goal)

# ただし、距離が0より小さい場合は、安全距離を確保
if target_distance < 0.1:
    target_distance = 0.1

# 目標までの距離が十分に確保されていない場合、前進と横歩きで近づく
# ロボットの向きに沿って移動するため、x方向とy方向の移動量を計算
# ロボットが前後方向に移動するため、目標点への距離を前後方向に投影
# ロボットの向き（current_yaw）から、cosとsinを使って移動方向を変換
# 目標点へのベクトルをロボットの向きに投影
cos_yaw = math.cos(math.radians(current_yaw))
sin_yaw = math.sin(math.radians(current_yaw))

# 前後方向（x方向）への距離成分
forward_distance = (blue_box_x - x) * cos_yaw + (blue_box_y - y) * sin_yaw

# 左右方向（y方向）への距離成分
lateral_distance = -(blue_box_x - x) * sin_yaw + (blue_box_y - y) * cos_yaw

# 前後方向の移動量を計算（安全距離を考慮）
# 前後方向に移動する速度を0.5 m/sで、横歩きは0.3 m/sで、安全に近づく
# 前後方向に移動するため、前後方向の距離を足して目標に近づく
# 横歩きは、目標点に近づくために必要

# 前後方向の移動量を安全に近づくようにする
# 前後方向の移動量を調整（安全距離を考慮）
target_forward = forward_distance
target_lateral = lateral_distance

# 1ステップで移動する距離を0.2mとし、最大120秒以内に到達するようにする
max_steps = 600  # 600ステップで最大120秒（0.1秒/ステップ）
step_size = 0.2

# 前後方向の移動と横歩きで、目標点に近づく
for step in range(max_steps):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの向きに沿った前後方向の距離
    cos_yaw = math.cos(math.radians(current_yaw))
    sin_yaw = math.sin(math.radians(current_yaw))
    
    # 目標点への距離
    dx = blue_box_x - x
    dy = blue_box_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    # 現在の位置から目標までの距離が安全距離を満たしているかチェック
    if dist <= 0.35:  # 安全距離（ロボットの前後幅0.35m）
        # 横歩きで調整して、箱の中心に近づく
        # 横歩きは、ロボットの向きに垂直な方向に移動
        # ただし、横歩きは0.3 m/sまで
        # 横歩きの速度を調整（距離が小さくなるほどゆっくりにする）
        if dist < 0.1:
            # ほぼ到達したので、静止
            break
        # 横歩きの速度を調整（距離が小さいほど小さく）
        lateral_speed = 0.3 * (1 - dist / 0.35)
        walk(0.0, lateral_speed, 0.0, duration=0.1)
    else:
        # 前後方向に移動
        forward_speed = 0.5
        walk(forward_speed, 0.0, 0.0, duration=0.1)

# 到達後、5秒間静止
stop(5.0)
```