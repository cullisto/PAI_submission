```python
# 赤い箱までの距離を計算し、障害物を避けながらその場で右に45度回ってから進むようにする
# 初期位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標位置：赤い箱の中心
target_x, target_y = get_object_position("red_box")

# ロボットの大きさを考慮して、箱に近づくための安全距離を設定（ロボットの中心から0.35m前後、0.15m左右）
# 赤い箱は (4.2, 0.0)、大きさ 0.3×0.3
# よって、ロボットの中心が (4.2 - 0.35, 0.0) から (4.2 + 0.35, 0.0) まで動けるが、左右は 0.15m より近づけない

# まず、ロボットの現在の向きを調整して、赤い箱に向かって進むようにする
# 現在の向きが0度（+x方向）なので、赤い箱に向かう方向（x軸）に近づくために、必要な角度を計算
target_yaw = math.degrees(math.atan2(target_y - y0, target_x - x0))

# 目標の向きに近づくまで旋回（左回りが正、右回りは負）
for _ in range(300):  # 最大 30 秒
    current_yaw = get_yaw()
    err_yaw = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err_yaw) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err_yaw)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 旋回が完了したら、安全な距離で前進
# 赤い箱までの距離を確認（ロボットの中心から）
distance_to_target = distance_to(target_x, target_y)

# 最大120秒以内で到達できるように、前進する
max_steps = 120
step_duration = 0.1
for step in range(int(max_steps / step_duration)):
    # 現在の位置を取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # ロボットの向きに沿って目標点へのベクトルを計算
    dx = target_x - x
    dy = target_y - y
    direction_angle = math.degrees(math.atan2(dy, dx))
    
    # 旋回を避けるために、現在の向きに近づけた上で、前進する
    # 前後速度を調整（最大1.0 m/s）
    vx = 0.8
    vy = 0.0
    
    # 障害物に近づかないように、各ステップで障害物との距離をチェック
    # wall_back: (3.0, 0.0), 大きさ 0.3×2.7
    # wall_left: (2.325, 1.2), 大きさ 1.65×0.3
    # wall_right: (2.325, -1.2), 大きさ 1.65×0.3
    
    # 各障害物との距離を計算（ロボットの中心から）
    wall_back_dist = distance_to(3.0, 0.0)
    wall_left_dist = distance_to(2.325, 1.2)
    wall_right_dist = distance_to(2.325, -1.2)
    
    # 障害物に近づかないように、安全距離を設定（ロボットの大きさを考慮）
    # 前後方向：ロボットの中心から0.35m（胴体の前後）
    # 左右方向：0.15m
    # ただし、壁の大きさも考慮（壁の中心から0.35m前後、0.15m左右）
    
    # 壁の中心からロボットの中心までの距離が、壁の大きさの半分より小さい場合、避ける
    # wall_back: 0.35m は安全距離（0.35mより近づかない）
    if wall_back_dist < 0.35:
        # 前進をやめる
        break
    
    # wall_left: 0.15m より近づかない（左右方向）
    if wall_left_dist < 0.15:
        break
    
    # wall_right: 0.15m より近づかない
    if wall_right_dist < 0.15:
        break
    
    # 前進
    walk(vx, vy, 0.0, duration=step_duration)
    
    # 到達判定（距離が0.5m以下なら終了）
    if distance_to(target_x, target_y) <= 0.5:
        break

# 到達後、少し止める
stop(0.5)
```