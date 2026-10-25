# 方針:
# 赤い箱はコの字の奥の壁 (wall_back) の外側にあるため、まっすぐ進むと壁に当たる。
# 右の壁 (wall_right) の外側を回り込み、奥の壁の裏側から箱に近づく。
#
# 壁の範囲（中心 ± 大きさ/2）:
#   wall_back : x 2.85〜3.15, y -1.35〜1.35
#   wall_right: x 1.50〜3.15, y -1.35〜-1.05
# Go2 の胴体は約 0.7 m × 0.3 m なので、壁から 0.5 m 以上離れたルートを通る。

# --- 物体情報から障害物の外周を計算 ---
objs = get_objects()
obstacles = [o for o in objs if o["is_obstacle"]]
min_y = min(o["y"] - o["size_y"] / 2 for o in obstacles)   # 障害物群の右端 (-1.35)
max_x = max(o["x"] + o["size_x"] / 2 for o in obstacles)   # 障害物群の奥端 (3.15)

bx, by = get_object_position("red_box")

margin = 0.65                      # 壁とのすき間
side_y = min_y - margin            # 回り込みルートの y (約 -2.0)
behind_x = max_x + margin          # 奥の壁の裏側の x (約 3.8)

# --- 経由点 ---
waypoints = [
    (1.0, side_y),        # 右壁の手前側の外側へ
    (behind_x, side_y),   # 右壁・奥壁の外側を通過
    (behind_x, by),       # 奥壁の裏側、箱の真横（手前）へ
]

for i, (wx, wy) in enumerate(waypoints):
    ok = move_to(wx, wy, tolerance=0.2, timeout=25.0)
    print("経由点", i, (round(wx, 2), round(wy, 2)), "到着:", ok, "現在位置:", get_position())

# --- 箱の手前まで近づく ---
# 箱の表面 (半幅 0.15) + ロボットの半身長 (約 0.35) 程度を残して止まる
face(bx, by)
x, y = get_position()
d = math.hypot(bx - x, by - y)
approach = 0.5
if d > approach:
    gx = bx - (bx - x) / d * approach
    gy = by - (by - y) / d * approach
    ok = move_to(gx, gy, tolerance=0.1, timeout=15.0)
    print("箱の手前に到着:", ok)

face(bx, by)
stop(0.5)
print("最終位置:", get_position(), "箱までの距離:", round(distance_to(bx, by), 2))
