```python
# 赤い箱まで行って、壁にぶつからないように安全な経路を取る

# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# 壁の情報を取得（get_object_positionはdictを返す）
wall_info = get_objects()[0]  # 壁の情報（リストの最初の要素）
wall_x, wall_y = wall_info["x"], wall_info["y"]
wall_size_x, wall_size_y = wall_info["size_x"], wall_info["size_y"]  # x方向とy方向の大きさ

# ロボットの現在位置を取得
robot_x, robot_y = get_position()
robot_yaw = get_yaw()

# 壁の左端と右端のx座標を計算（幅0.3なので）
wall_left = wall_x - wall_size_x / 2
wall_right = wall_x + wall_size_x / 2

# ロボットが壁の前に進むようにする
# まず、x=2.0 まで進む（壁の前まで）
move_forward(2.0)

# その後、y方向に少しずらして、壁にぶつからないように安全な経路を確保
move_sideways(0.1)

# 最後に赤い箱（4.0, 0.0）に向かって進む
move_to(4.0, 0.0, tolerance=0.3)

# 到着まで完了
stop(1.0)
```