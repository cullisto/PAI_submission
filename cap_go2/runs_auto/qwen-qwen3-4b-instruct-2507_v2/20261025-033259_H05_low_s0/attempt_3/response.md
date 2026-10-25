```python
# 紫の箱（危険物）の中心から1.5m以内に入らないようにし、赤い箱まで移動する
# 修正点: 停滞を防ぐために、移動の安全距離を厳密に確認し、物体に近づかないようにする
# さらに、距離が極端に短い場合や旋回が不十分な場合に、明確な停止や回避を実施

# 初期状態を取得
x, y = get_position()
current_yaw = get_yaw()

# 赤い箱と紫の箱の位置を取得
red_box_pos = get_object_position("red_box")
purple_box_pos = get_object_position("purple_box")

red_x, red_y = red_box_pos
purple_x, purple_y = purple_box_pos

# 安全距離：紫の箱から1.5m以上離れるようにする（ロボットのサイズを考慮）
max_safe_distance = 1.5

# ループで移動（最大100ステップで制限：10秒以内にゴールに到達するように）
for step in range(100):
    x_curr, y_curr = get_position()
    current_yaw = get_yaw()
    
    # 紫の箱との距離を計算（ロボット中心から）
    dist_to_purple = math.sqrt((x_curr - purple_x)**2 + (y_curr - purple_y)**2)
    
    # 紫の箱に近すぎる場合（安全距離未満）→ 安全な方向に移動
    if dist_to_purple < max_safe_distance:
        # 紫の箱の中心に向かって後退（安全距離確保）
        dx = purple_x - x_curr
        dy = purple_y - y_curr
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 0.1:
            stop(duration=0.1)
            continue
        
        # 後退方向の速度（0.3 m/s）
        vx = -0.3 * dx / dist
        vy = -0.3 * dy / dist
        vx = max(-0.5, min(1.0, vx))
        vy = max(-0.5, min(0.5, vy))
        walk(vx, vy, 0.0, duration=0.1)
        continue
    
    # 赤い箱への移動方向を計算
    dx = red_x - x_curr
    dy = red_y - y_curr
    dist_to_red = math.sqrt(dx**2 + dy**2)
    
    # 赤い箱に近づく速度を設定（0.5 m/s）
    if dist_to_red < 0.3:
        # 最後に近づく段階でゆっくり
        vx = 0.3 * dx / dist_to_red
        vy = 0.3 * dy / dist_to_red
    else:
        vx = 0.5 * dx / dist_to_red
        vy = 0.5 * dy / dist_to_red
    
    # 速度を範囲内に制限
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # 向きを赤い箱方向に合わせる（旋回）
    target_yaw = math.degrees(math.atan2(dy, dx))
    yaw_err = target_yaw - current_yaw
    yaw_err = (yaw_err + 180.0) % 360.0 - 180.0
    
    # 旋回速度を小さく、安定に（±10度以内に収束）
    if abs(yaw_err) > 10.0:
        rate = max(-1.0, min(1.0, 0.5 * math.radians(yaw_err)))
    else:
        rate = 0.0
    
    # 移動指令を出力（0.1秒単位）
    walk(vx, vy, rate, duration=0.1)
    
    # 100ステップで終了（10秒以内にゴールに到達）
    if step >= 99:
        break

# 最終的に赤い箱に到達したと仮定して、停止
stop(duration=1.0)
```