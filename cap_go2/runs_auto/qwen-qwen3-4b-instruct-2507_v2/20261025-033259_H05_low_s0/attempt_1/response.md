```python
# 紫の箱（危険物）の中心から1.5m以内に入らないようにし、赤い箱まで移動する
# ステップ1: 紫の箱の位置を取得し、ロボットがその範囲内に近づかないようにする
# ステップ2: 赤い箱に向かって移動するが、紫の箱との距離を常に1.5m以上に保つ

# 初期状態を取得
x0, y0 = get_position()
current_yaw = get_yaw()

# 赤い箱と紫の箱の位置を取得
red_box_pos = get_object_position("red_box")
purple_box_pos = get_object_position("purple_box")

# 各物体の中心座標
red_x, red_y = red_box_pos
purple_x, purple_y = purple_box_pos

# 目標：赤い箱に向かって進むが、紫の箱に1.5m以内に入らないようにする
# ロボットのサイズを考慮して、紫の箱の中心からロボットの前後方向に0.35m（半径）の安全距離を確保
# つまり、ロボットの中心が紫の箱の中心から1.5m以上離れるようにする

max_safe_distance = 1.5  # 紫の箱との安全距離

# ループで移動（最大120秒まで）
for _ in range(1200):  # 1秒ごとに1ステップ（0.1秒ごとの更新を想定）
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 紫の箱との距離を計算（ロボット中心から）
    dist_to_purple = math.sqrt((x - purple_x)**2 + (y - purple_y)**2)
    
    # 紫の箱に近すぎる場合は、安全距離を確保するため、紫の箱に向かって後退または回転
    if dist_to_purple < max_safe_distance:
        # 紫の箱に近いので、安全な方向に移動（紫の箱の中心に向かって後退）
        # まず、紫の箱に向かうベクトルを計算
        dx = purple_x - x
        dy = purple_y - y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 0.1:  # 非常に近い場合
            # そのまま止まる
            stop(duration=0.1)
            continue
        
        # 紫の箱に向かって後退（安全距離を確保するため）
        # ベクトル方向に後退する（-x方向の速度）
        unit_x = dx / dist
        unit_y = dy / dist
        # 速度を調整（後退速度は0.3 m/s）
        vx = -0.3 * unit_x
        vy = -0.3 * unit_y
        # ただし、速度は範囲内に収める
        vx = max(-0.5, min(1.0, vx))
        vy = max(-0.5, min(0.5, vy))
        walk(vx, vy, 0.0, duration=0.1)
        continue
    
    # 紫の箱から安全距離を確保した状態で、赤い箱に向かって進む
    # 赤い箱に向かう方向のベクトルを計算
    dx = red_x - x
    dy = red_y - y
    dist_to_red = math.sqrt(dx**2 + dy**2)
    
    # 赤い箱に近づく速度を設定（前進速度0.5 m/s）
    if dist_to_red < 0.5:  # 赤い箱に近づいたら、ゆっくり前進
        vx = 0.5
        vy = 0.0
    else:
        # 赤い箱に向かって前進
        unit_x = dx / dist_to_red
        unit_y = dy / dist_to_red
        vx = 0.5 * unit_x
        vy = 0.5 * unit_y
    
    # 速度を範囲内に制限
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # ロボットの向きが赤い箱方向と一致していない場合、少しずつ向きを調整
    # 赤い箱方向のベクトルと現在の向きの差を計算
    target_yaw = math.degrees(math.atan2(dy, dx))
    yaw_err = target_yaw - current_yaw
    # 角度の差を-180〜180に収める
    yaw_err = (yaw_err + 180.0) % 360.0 - 180.0
    
    # 旋回速度を調整（小さく、安定）
    if abs(yaw_err) > 5.0:
        rate = max(-1.0, min(1.0, 0.5 * math.radians(yaw_err)))
    else:
        rate = 0.0
    
    # 速度と旋回を組み合わせて移動
    walk(vx, vy, rate, duration=0.1)
    
    # シミュレーション時間制限（120秒）
    if _ >= 1200:
        break

# 最終的に赤い箱に到達したと仮定して、停止
stop(duration=1.0)
```