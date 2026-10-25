# 箱（名前に "box" を含む物体）の中から、現在位置から一番近いものを探す
x, y = get_position()
boxes = [o for o in get_objects() if "box" in o["name"]]

nearest = None
nearest_d = float("inf")
for o in boxes:
    d = math.hypot(o["x"] - x, o["y"] - y)
    print(o["name"], "までの距離:", round(d, 2))
    if d < nearest_d:
        nearest_d = d
        nearest = o

print("一番近い箱:", nearest["name"], "距離:", round(nearest_d, 2))

bx, by = nearest["x"], nearest["y"]

# まず箱の方を向く
face(bx, by)

# 箱の中心にはぶつかるので、箱の半分の大きさ＋余裕を取った手前の点を目標にする
margin = max(nearest["size_x"], nearest["size_y"]) / 2.0 + 0.35
x, y = get_position()
d = math.hypot(bx - x, by - y)
if d > margin:
    gx = bx - (bx - x) / d * margin
    gy = by - (by - y) / d * margin
    reached = move_to(gx, gy, tolerance=0.15, timeout=30.0)
    print("到着:", reached)

# 最後に箱の方を向き直して静止
face(bx, by)
stop(0.5)
print("最終位置:", get_position())
