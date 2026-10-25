# 赤い箱までの道を計画する。壁があるため、直接進むのは危険。
# 壁の中心は (2.0, 0.0)、大きさは 0.3×1.6（y方向が1.6m）。ロボットは (0.0, 0.0) から出発。
# 赤い箱は (4.0, 0.0) にあるが、壁があるため、y方向にずらして通る必要がある。

# まず、壁の位置と大きさを確認
objects = get_objects()
wall_obj = None
for obj in objects:
    if obj["name"] == "wall":
        wall_obj = obj
        break

# 壁の中心と大きさを確認（y方向が幅）
wall_x, wall_y = wall_obj["x"], wall_obj["y"]
wall_size_x, wall_size_y = wall_obj["size_x"], wall_obj["size_y"]

# 壁のy方向の範囲（y軸の上下）
wall_bottom = wall_y - wall_size_y / 2
wall_top = wall_y + wall_size_y / 2

# ロボットの現在位置と向き
x, y = get_position()
current_yaw = get_yaw()

# 最初はx軸方向（0度）に動くが、壁にぶつからないようにy方向にずらす。
# 壁は (2.0, 0.0) で、高さが1.6mなので、y方向に±0.8mの範囲に注意。
# よって、y方向に0.4mずらして進むことで、壁に近づきすぎず安全に進める。

# まず、y方向に0.4m右にずらして、壁の前に進む（x方向に進む）
# ただし、壁の前に到達する前にy方向に少し移動する必要がある。

# 1. まず、x軸方向に進む前に、y方向に0.4m右にずらす（ロボットの向きが0度なので、右は負）
move_sideways(0.4)

# 2. その後、x方向に進む（壁の前に到達するまで）
# 壁は (2.0, 0.0)、ロボットは (0.0, 0.4) なので、x方向に2.0m進む必要がある
# ただし、壁のy方向範囲を考慮して、x方向に進むとy方向がずれるので、壁にぶつからないようにする。

# 3. まず、壁の前に到達するまでx方向に進む
move_forward(2.0)

# 4. ここで、壁のy方向範囲内にいるか確認（壁のyは0.0、大きさ1.6mなので、y方向に±0.8mまでOK）
# 現在の位置を確認
x, y = get_position()
print(f"現在位置: ({x}, {y})")

# 5. 赤い箱まで進む（x=4.0, y=0.0）→ 今いる位置からx方向に2.0m進む
# ただし、y方向は0.4mなので、赤い箱に近づくにはy方向に0.4m戻る必要がある
move_sideways(-0.4)

# 6. 赤い箱に向かって進む（x方向に2.0m）
move_forward(4.0)

# 7. 到着確認（赤い箱の中心 (4.0, 0.0) まで到達）
# 距離が0.3m以内なら到着とみなす
target_x, target_y = 4.0, 0.0
distance = math.hypot(target_x - x, target_y - y)
print(f"赤い箱までの距離: {distance:.2f}m")

# 距離が0.3m以内なら、到着とみなす
if distance <= 0.3:
    print("赤い箱に到達しました。")
else:
    # まだ到着していない場合は、少し近づく
    move_forward(0.5)

# 最後に停止
stop(1.0)
