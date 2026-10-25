# 赤い箱の位置を取得
bx, by = get_object_position("red_box")

# まず箱の方を向く
face(bx, by)

# 箱の中心から 0.55 m 手前（ロボット側）を目標にする
# （箱の半幅 0.15 m + ロボット前方の半長 0.35 m = 0.5 m に少し余裕を持たせる）
x, y = get_position()
d = math.hypot(bx - x, by - y)
approach = 0.55
if d > approach:
    gx = bx - (bx - x) / d * approach
    gy = by - (by - y) / d * approach
    reached = move_to(gx, gy, tolerance=0.15, timeout=30.0)
    print("到着:", reached)
else:
    print("すでに箱の近くにいます")

# 最後に箱の方を向き直して静止
face(bx, by)
stop(0.5)
print("現在位置:", get_position(), "向き:", get_yaw(), "箱までの距離:", distance_to(bx, by))
