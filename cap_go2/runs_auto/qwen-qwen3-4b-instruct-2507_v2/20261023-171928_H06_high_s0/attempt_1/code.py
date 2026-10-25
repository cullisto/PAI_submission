# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを確認
current_x, current_y = get_position()
current_yaw = get_yaw()

# 赤い箱に向かって向きを調整する（お尻を向けるため、箱の反対方向を向く）
# お尻を向ける = ロボットの向きが +x 方向（0 deg）に対して 180 deg になる
target_yaw = 180.0  # お尻を向けるための向き（x軸の反対方向）

# その場で旋回して、赤い箱の反対方向（お尻を向ける方向）を向く
turn_to(target_yaw)

# 赤い箱の中心から1メートル離れた位置を計算（ロボットの中心が箱の表面から0.35m前後まで近づけないため）
# 赤い箱の中心から0.35m離れた位置を計算（ロボットの前後方向に）
safe_distance = 1.0  # 箱から1メートル離れる
dx = red_box_x - current_x
dy = red_box_y - current_y
distance = math.hypot(dx, dy)

# 1メートル離れた位置を計算（距離が0なら、そのままの位置に1m離れた点を設定）
if distance == 0:
    target_x = current_x
    target_y = current_y
else:
    # ロボットが箱の中心から0.35m前後まで近づけないため、1m離れた点を計算
    # ただし、ロボットが箱の中心に近づくと当たるため、安全な距離を確保
    # 1m離れた点は、箱の中心から1m離れた方向に進む
    target_x = red_box_x - (dx / distance) * (safe_distance)
    target_y = red_box_y - (dy / distance) * (safe_distance)

# その位置まで移動（安全な距離を確保）
reached = move_to(target_x, target_y, tolerance=0.15)
print("目標位置に到達:", reached)

# 到達したら停止
if reached:
    stop(2.0)
