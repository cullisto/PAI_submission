# 赤い箱の位置を取得
bx, by = get_object_position("red_box")
x, y = get_position()

# まず箱の方を向く
face(bx, by)

# 箱の中心にはぶつかって入れないので、箱の中心から 0.5 m 手前（ロボット側）を目標にする
d = math.hypot(bx - x, by - y)
if d > 0.5:
    gx = bx - (bx - x) / d * 0.5
    gy = by - (by - y) / d * 0.5
    reached = move_to(gx, gy, tolerance=0.15, timeout=30.0)
    print("到着:", reached)
else:
    print("すでに赤い箱の近くにいます")

# 最後に箱の方を向き直して静止
face(bx, by)
print("現在位置:", get_position(), "赤い箱までの距離:", distance_to(bx, by))
stop(0.5)
