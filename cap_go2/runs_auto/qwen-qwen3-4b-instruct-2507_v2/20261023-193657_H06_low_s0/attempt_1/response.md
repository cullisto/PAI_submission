```python
# 赤い箱の位置を取得し、ロボットがその箱に「お尻を向けて」1メートル離れた位置に到達するように制御する
# お尻を向ける = ロボットの向きが赤い箱の中心に対して180度（後ろ）を向く

# 赤い箱の中心座標を取得
red_box_x, red_box_y = get_object_position("red_box")

# 目標位置: 赤い箱の中心からロボットの前後方向に1メートル離れた位置（お尻を向けるため、後ろに1m）
# ロボットの向きが赤い箱に対して180度になるようにする（後ろを向く）
target_x = red_box_x
target_y = red_box_y

# ロボットの現在の位置と向きを取得
x, y = get_position()
yaw = get_yaw()

# 目標の向き: 赤い箱の中心に対して後ろを向く（180度）
# つまり、ロボットが赤い箱の中心に向かう方向に対して180度回転
# 現在の向き（yaw）から、赤い箱の中心方向（x軸から）の角度を計算
# 赤い箱の中心方向の角度（ロボットの前が正）は atan2(y - y, x - x)
# その方向に180度を足す（後ろを向く）
target_yaw = (math.degrees(math.atan2(red_box_y - y, red_box_x - x)) + 180.0) % 360.0

# ロボットの向きが目標の向きに近づくまで旋回（後ろを向く）
for _ in range(300):  # 最大30秒
    current_yaw = get_yaw()
    # ループ内で現在の向きを取得し、目標との差を計算（-180〜180度で扱う）
    yaw_diff = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(yaw_diff) < 3.0:  # 向きが十分に近づいたら終了
        break
    
    # 旋回の角速度を計算（左回りが正なので、後ろを向くには右回り（負））
    rate = max(-1.0, min(1.0, -2.0 * math.radians(yaw_diff)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# 旋回が終わったら、目標位置まで移動（1メートル離れた位置に到達）
# 1メートル離れた位置は、赤い箱の中心からロボットの前後方向に1m離れた点
# つまり、ロボットが赤い箱の中心に対して後ろに1m離れた点に到達する
# その位置は、赤い箱の中心からロボットの向きに反対方向に1m
target_x = red_box_x
target_y = red_box_y

# 目標位置に到達するまで移動（前後方向に1m）
# まず、ロボットの現在位置から目標位置までの距離を計算
current_x, current_y = get_position()
distance_to_target = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)

# 1メートル離れた位置に到達するまで移動（前後方向に1m）
# ただし、ロボットの向きに沿って移動する（後ろを向いている）
# よって、目標位置は、赤い箱の中心からロボットの向きの反対方向に1m
# つまり、移動方向は (red_box_x - x, red_box_y - y) の方向に1m
# しかし、ロボットは後ろを向いているので、移動方向はその反対（後ろ）

# まず、移動方向の単位ベクトルを計算（後ろを向く方向）
# つまり、赤い箱の中心からロボットの中心に向かうベクトルを反転
dx = red_box_x - current_x
dy = red_box_y - current_y
distance = math.sqrt(dx**2 + dy**2)
if distance > 0:
    # 向きを後ろにした上で、1m離れた位置に到達するため、後ろ方向に1m移動
    # つまり、移動方向は (dx, dy) の反対方向
    move_x = -dx / distance
    move_y = -dy / distance
    target_x = current_x + move_x
    target_y = current_y + move_y
else:
    # 位置が同じなら、そのまま
    target_x = current_x
    target_y = current_y

# 目標位置に1m離れた位置に到達するまで移動（前後方向に1m）
# 1m移動するまで前進（後ろを向いているので、後ろに進む）
# ただし、距離が1mを超えると止まる
max_distance = 1.0
for _ in range(300):  # 最大30秒
    x, y = get_position()
    dist_to_target = math.sqrt((target_x - x)**2 + (target_y - y)**2)
    if dist_to_target <= max_distance:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(0.5)
```