# 赤い箱（ゴール）と壁（障害物）の情報を取得
bx, by = get_object_position("red_box")
objs = get_objects()
wall = [o for o in objs if o["name"] == "wall"][0]

# 壁の範囲を計算: x 1.85〜2.15, y -0.8〜0.8
wall_x_min = wall["x"] - wall["size_x"] / 2
wall_x_max = wall["x"] + wall["size_x"] / 2
wall_y_max = wall["y"] + wall["size_y"] / 2

# 壁の左側（+y 側）を回り込む。
# ロボットの左右の半幅 0.15 m に余裕 0.35 m を足して、壁の端から 0.5 m 離れた y を通る
side_y = wall_y_max + 0.5          # = 1.3
# 壁の手前と奥の通過点。前後の半長 0.35 m に余裕を足す
before_x = wall_x_min - 0.65       # = 1.2
after_x = wall_x_max + 0.85        # = 3.0

waypoints = [
    (before_x, side_y),   # 壁の手前、左側に出る
    (after_x, side_y),    # 壁の横を通過して奥へ
    (after_x, by + 0.3),  # 箱の正面側のラインまで戻る
]

for i, (wx, wy) in enumerate(waypoints):
    ok = move_to(wx, wy, tolerance=0.2, timeout=25.0)
    print("経由点", i, (wx, wy), "到着:", ok, "現在位置:", get_position())

# 箱の方を向いてから、箱の中心から 0.5 m 手前まで進む
# （箱の表面 0.15 m + ロボットの前半分 0.35 m = 0.5 m で接触するため、少し余裕を持つ）
face(bx, by)
x, y = get_position()
d = math.hypot(bx - x, by - y)
stop_dist = 0.55
gx = bx - (bx - x) / d * stop_dist
gy = by - (by - y) / d * stop_dist
reached = move_to(gx, gy, tolerance=0.1, timeout=20.0)

# 最後に箱の方へ向きを合わせて停止
face(bx, by)
stop(0.5)
print("赤い箱に到着:", reached, "位置:", get_position(), "箱までの距離:", distance_to(bx, by))
