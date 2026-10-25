# 青い箱の裏側（スタート地点から見て箱の反対側）へ回り込み、箱の方を向いて止まる。
# 直進すると箱にぶつかるので、箱の周りを半径 0.9 m の円弧状の経由点で迂回する。

bx, by = get_object_position("blue_box")
sx, sy = get_position()  # スタート地点 (0, 0)

# スタート→箱 の単位ベクトル
dx, dy = bx - sx, by - sy
d = math.hypot(dx, dy)
ux, uy = dx / d, dy / d

# 最終目標: 箱の中心からスタートと反対方向に 0.7 m の点
# （正面から箱に向くと胴体前端までの距離は 0.15 + 0.35 = 0.5 m なので余裕を持たせる）
GOAL_R = 0.7
gx, gy = bx + ux * GOAL_R, by + uy * GOAL_R

# 迂回用の経由点（箱中心から半径 CLEAR_R の円上）
CLEAR_R = 0.9
base = math.atan2(-uy, -ux)  # 箱から見たスタート地点の方向


def point_at(angle_deg):
    a = base + math.radians(angle_deg)
    return (bx + CLEAR_R * math.cos(a), by + CLEAR_R * math.sin(a))


# 左回り・右回りの 2 案を作り、他の物体から遠い方を選ぶ
others = [o for o in get_objects() if o["name"] != "blue_box"]


def min_clearance(points):
    m = 1e9
    for (px, py) in points:
        for o in others:
            m = min(m, math.hypot(px - o["x"], py - o["y"]))
    return m


candidates = []
for sign in (1, -1):
    wps = [point_at(sign * 90), point_at(sign * 135)]
    candidates.append((min_clearance(wps), wps))
candidates.sort(key=lambda c: c[0], reverse=True)
waypoints = candidates[0][1]
print("経由点:", waypoints, "最終目標:", (gx, gy))

# 経由点を順にたどる
for (wx, wy) in waypoints:
    ok = move_to(wx, wy, tolerance=0.25, timeout=30.0)
    print("経由点到着:", ok, get_position())

# 裏側の目標地点へ
reached = move_to(gx, gy, tolerance=0.15, timeout=20.0)
print("裏側に到着:", reached, get_position())

# 青い箱の方を向いて止まる
face(bx, by)
stop(1.0)
print("最終位置:", get_position(), "向き:", get_yaw())
