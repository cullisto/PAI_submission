# 現在位置を取得
x, y = get_position()

# シーン内の物体から「箱」だけを取り出し、一番近いものを選ぶ
boxes = [o for o in get_objects() if "box" in o["name"]]
nearest = None
nearest_d = float("inf")
for o in boxes:
    d = math.hypot(o["x"] - x, o["y"] - y)
    print(o["name"], "までの距離: {:.2f} m".format(d))
    if d < nearest_d:
        nearest_d = d
        nearest = o

print("一番近い箱:", nearest["name"], "({:.2f} m)".format(nearest_d))
bx, by = nearest["x"], nearest["y"]

# まず箱の方を向く（正面から近づくため）
face(bx, by)

# 正面から近づくと、箱の半分の大きさ + ロボット前半分(約0.35 m)で当たるので、
# 少し余裕を持たせて箱の中心から手前の点を目標にする
half = max(nearest["size_x"], nearest["size_y"]) / 2.0
stop_dist = half + 0.35 + 0.05  # 0.3 m の箱なら 0.55 m
x, y = get_position()
d = math.hypot(bx - x, by - y)
if d > stop_dist:
    gx = bx - (bx - x) / d * stop_dist
    gy = by - (by - y) / d * stop_dist
    reached = move_to(gx, gy, tolerance=0.1, timeout=30.0)
    print("到着:", reached)
else:
    print("すでに箱の近くにいます")

# 最後にもう一度箱の方を向いて静止
face(bx, by)
stop(0.5)
x, y = get_position()
print("最終位置: ({:.2f}, {:.2f}), 箱までの距離: {:.2f} m".format(x, y, distance_to(bx, by)))
