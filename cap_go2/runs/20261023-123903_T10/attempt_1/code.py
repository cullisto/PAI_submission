# 壁を左側（+y 側）から回り込んで赤い箱の手前まで行く
# move_to は障害物を避けないので、壁の外側を通る経由点を順にたどる

# --- 物体の情報を取得 ---
objs = get_objects()
wall = None
for o in objs:
    if o["name"] == "wall":
        wall = o
bx, by = get_object_position("red_box")

# 壁の範囲（中心 ± 大きさ/2）
wx_min = wall["x"] - wall["size_x"] / 2.0   # 1.85
wx_max = wall["x"] + wall["size_x"] / 2.0   # 2.15
wy_min = wall["y"] - wall["size_y"] / 2.0   # -0.8
wy_max = wall["y"] + wall["size_y"] / 2.0   #  0.8

# ロボットの胴体（長さ約 0.7 m、幅約 0.3 m）を考慮した安全マージン
MARGIN_Y = 0.6   # 壁の端から横方向に離れる距離
MARGIN_X = 0.65  # 壁の前後から離れる距離

# 現在位置から近い側（左右）を選んで回り込む
x0, y0 = get_position()
if abs(y0 - wy_max) <= abs(y0 - wy_min):
    side_y = wy_max + MARGIN_Y   # 左側（+y）を通る: y = 1.4
else:
    side_y = wy_min - MARGIN_Y   # 右側（-y）を通る

# 経由点: 壁の手前の横 → 壁の向こう側の横
waypoints = [
    (wx_min - MARGIN_X, side_y),  # (1.2, 1.4)
    (wx_max + MARGIN_X, side_y),  # (2.8, 1.4)
]

for i, (gx, gy) in enumerate(waypoints):
    ok = move_to(gx, gy, tolerance=0.15, timeout=25.0)
    print("経由点", i + 1, (round(gx, 2), round(gy, 2)), "到着:", ok, "現在位置:", get_position())

# --- 赤い箱の手前まで進む ---
# 箱の中心にはぶつかるので、箱の中心から 0.45 m 手前（ロボット側）を目標にする
face(bx, by)
x, y = get_position()
d = math.hypot(bx - x, by - y)
gx = bx - (bx - x) / d * 0.45
gy = by - (by - y) / d * 0.45
reached = move_to(gx, gy, tolerance=0.15, timeout=25.0)

# 最後に箱の方を向いて静止
face(bx, by)
stop(0.5)
print("赤い箱に到着:", reached, "位置:", get_position(), "箱までの距離:", round(distance_to(bx, by), 2))
