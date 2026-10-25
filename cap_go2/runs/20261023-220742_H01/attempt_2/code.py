# 青い箱の裏側（スタート地点から見て反対側）に回り込み、箱の方を向いて止まる。
# 箱に直進するとぶつかるので、箱の周りに半径 R の円を考え、
# 円周上の経由点をたどって横から回り込む。

bx, by = get_object_position("blue_box")
sx, sy = get_position()  # スタート地点

R = 0.8  # 箱の中心から保つ距離 [m]（箱の半幅 0.15 + ロボットの体の大きさ + 余裕）

# 箱から見たスタート地点の方向（角度）
start_ang = math.atan2(sy - by, sx - bx)
# 裏側 = スタート地点の反対方向（180 度回った位置）
goal_ang = start_ang + math.pi

# 左回り（反時計回り）で回り込む。45 度刻みで経由点を作る
# （開始側から 90 度ずれた横の点から、裏側の点まで）
steps = 4  # 90 deg -> 180 deg を 45 deg ずつ: 90, 135, 180 の 3 点 + 余裕
waypoints = []
for i in range(2, 5):  # i=2:90deg, i=3:135deg, i=4:180deg
    a = start_ang + math.radians(45 * i)
    waypoints.append((bx + R * math.cos(a), by + R * math.sin(a)))

# まず横の経由点へ向かう前に、スタート→最初の経由点の直線が箱に近すぎないか確認し、
# 近すぎる場合は 45 度の点も追加する
def seg_dist(px, py, ax, ay, qx, qy):
    # 点 (px,py) と線分 (ax,ay)-(qx,qy) の距離
    dx, dy = qx - ax, qy - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

if seg_dist(bx, by, sx, sy, waypoints[0][0], waypoints[0][1]) < R * 0.8:
    a = start_ang + math.radians(45)
    waypoints.insert(0, (bx + R * math.cos(a), by + R * math.sin(a)))

# 経由点を順にたどる（最後が裏側の目標点）
for i, (wx, wy) in enumerate(waypoints):
    last = (i == len(waypoints) - 1)
    tol = 0.1 if last else 0.2
    ok = move_to(wx, wy, tolerance=tol, timeout=25.0)
    print("経由点", i, "(%.2f, %.2f) 到着:" % (wx, wy), ok)

# 青い箱の方を向いて止まる
face(bx, by)
stop(1.0)

x, y = get_position()
print("最終位置: (%.2f, %.2f), 向き: %.1f deg, 箱までの距離: %.2f m"
      % (x, y, get_yaw(), distance_to(bx, by)))
