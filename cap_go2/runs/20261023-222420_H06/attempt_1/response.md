# 赤い箱の中心位置を取得
bx, by = get_object_position("red_box")
x, y = get_position()

# 箱からロボットへ向かう方向の単位ベクトル（箱から見てロボット側に止まる）
d = math.hypot(x - bx, y - by)
if d < 1e-6:
    ux, uy = -1.0, 0.0  # 念のため（重なっている場合は -x 側を使う）
else:
    ux, uy = (x - bx) / d, (y - by) / d

# 目標地点: 箱の中心から 1.0 m 離れた点（ロボット側）
target_dist = 1.0
gx = bx + ux * target_dist
gy = by + uy * target_dist
print("目標地点:", (round(gx, 3), round(gy, 3)))

# 目標地点まで歩く
reached = move_to(gx, gy, tolerance=0.1, timeout=30.0)
print("到着:", reached)

# お尻を箱に向ける = 箱と反対方向を向く
x, y = get_position()
away_yaw = math.degrees(math.atan2(y - by, x - bx))
turn_to(away_yaw)

# 距離の微調整（箱に背を向けているので、前進すると箱から離れる）
for _ in range(3):
    x, y = get_position()
    err = target_dist - math.hypot(x - bx, y - by)
    if abs(err) < 0.05:
        break
    move_forward(err)
    # 向きのずれを補正
    x, y = get_position()
    turn_to(math.degrees(math.atan2(y - by, x - bx)))

stop(1.0)
x, y = get_position()
print("最終位置:", (round(x, 3), round(y, 3)),
      "箱までの距離:", round(math.hypot(x - bx, y - by), 3),
      "向き:", round(get_yaw(), 1))
