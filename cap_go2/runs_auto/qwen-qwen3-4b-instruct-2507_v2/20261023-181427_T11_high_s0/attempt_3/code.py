# 赤い箱まで行って、壁にぶつからないように安全な経路で進む
# 前回の失敗は、壁に近づく前に y 方向の安全距離を確保できず、x 方向に進む際に壁に接触したため
# 修正点:
# 1. 初期状態で y 方向に安全距離（0.15m）を確保（壁の y 方向範囲 ±0.8 から 0.15m 離れる）
# 2. 壁に近づく前に、x 方向に進むのではなく、壁の影響を避けるために、x 方向に進む前に旋回して安全な向きに移る
# 3. 赤い箱に向かって、壁の影響を考慮した経路（y 方向にずらして進む）を取る
# 4. move_to を使うのではなく、安全な位置に到達するまで手動で制御（壁にぶつからないように）

# 赤い箱の位置
red_box_x, red_box_y = get_object_position("red_box")

# 壁の位置と大きさ
wall_x, wall_y = 2.0, 0.0
wall_size_x, wall_size_y = 0.3, 1.6

# ロボットの現在位置
robot_x, robot_y = get_position()
robot_yaw = get_yaw()

# 壁の y 方向範囲: -0.8 ～ +0.8 → ロボットの y が ±0.15m 以内だと当たる
# よって、y 方向に 0.15m 以上離れる必要がある

# まず、y 方向に 0.15m 進む（安全な位置に移動）
move_sideways(0.15)

# 次に、壁に近づく前に、x 方向に進むが、x=2.0 に近づく前に安全な位置に到達するようにする
# つまり、x 方向に進む前に、壁に近づく距離を計算し、安全な範囲（x < 2.0）で進む

# 赤い箱までの距離を計算
dx = red_box_x - robot_x
dy = red_box_y - robot_y
distance = math.hypot(dx, dy)

# 壁に近づく距離（x 方向）
wall_distance = abs(wall_x - robot_x)

# 壁に近づく前に、x 方向に進むが、x=2.0 に達する前に安全に進む
# 進む距離は、x=2.0 までに近づく距離を計算
max_x_to_reach = 2.0
safe_x_distance = max_x_to_reach - robot_x
if safe_x_distance > 0:
    # x 方向に安全な速度で進む（0.5 m/s）
    move_forward(safe_x_distance * 0.5)

# その後、赤い箱に向かって、安全な y 方向で直進（壁にぶつからないように）
# ここで、move_to を使うが、壁に近づく前に y 方向を維持

# ただし、move_to は障害物を避けることがないため、安全な経路を手動で確保
# よって、赤い箱に向かって、壁に近づく前に、x 方向に進むようにする

# 安全な経路として、y 方向を 0.15m で維持し、x 方向に進む
# そのため、赤い箱に向かって、x 方向に進むが、x=2.0 に達する前に y 方向を維持

# まず、赤い箱に向かって、壁に近づく前に、x 方向に進む
# 進む距離は、x=2.0 までに近づく距離を計算
safe_x_distance = max_x_to_reach - robot_x
if safe_x_distance > 0:
    move_forward(safe_x_distance * 0.5)

# その後、赤い箱に向かって、y 方向を維持しながら進む
# ただし、x 方向に進むことで安全に赤い箱に近づく

# 現在の位置を取得
current_x, current_y = get_position()

# 赤い箱までの距離を再計算
dx = red_box_x - current_x
dy = red_box_y - current_y
final_distance = math.hypot(dx, dy)

# 最終的に赤い箱に近づく
# 安全な距離（0.3m）以内に達するまで、安全な速度で進む
vx = 0.5  # 前後の速度（安全）
vy = 0.0  # 左右の速度（y 方向を維持）

# 直進するため、現在の向きを赤い箱に向ける
face(red_box_x, red_box_y)

# その後、安全な距離まで直進
move_forward(final_distance * 0.5)

# 最終的に赤い箱に到達するまで、安全に進む
reached = move_to(red_box_x, red_box_y, tolerance=0.3)
print("赤い箱に到着:", reached)

if reached:
    stop(1.0)
