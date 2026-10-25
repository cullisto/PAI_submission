```python
# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")
# ロボットの現在位置を取得
current_x, current_y = get_position()
current_yaw = get_yaw()

# 赤い箱までの距離を計算
distance = math.hypot(red_box_x - current_x, red_box_y - current_y)

# ロボットのサイズを考慮して、箱に近づく際の安全距離を確保（胴体の前後幅 0.35m を考慮）
# 箱の中心からロボットの中心が近づくのは、0.35m 以上離す必要がある（正面から）
safe_distance = 0.35  # ロボットの前後方向の安全距離

# 箱に近づく前に、向きを調整して、正面で向くようにする（箱の中心を向く）
# まず、箱の中心を向く
face(red_box_x, red_box_y)

# さらに安全な距離を確保するために、目標位置を箱の中心から安全距離だけ手前へずらす
# ロボットの向きに応じて、手前の位置を計算
dx = red_box_x - current_x
dy = red_box_y - current_y
distance_to_target = math.hypot(dx, dy)

# 0.35m 未満の距離なら、直接移動せず、安全な距離を確保してから進む
if distance_to_target < safe_distance:
    # 距離が安全距離未満なら、そのまま停止
    print("距離が安全距離未満。停止します。")
    stop(1.0)
else:
    # 安全な距離を確保した目標位置を計算（箱の中心から安全距離手前）
    target_distance = distance_to_target - safe_distance
    target_x = current_x + (dx / distance_to_target) * target_distance
    target_y = current_y + (dy / distance_to_target) * target_distance
    
    # 安全な距離で移動する
    reached = move_to(target_x, target_y, tolerance=0.15)
    print("安全距離を確保して目標へ到達:", reached)
    if reached:
        stop(1.0)
```