# 方針:
# 1. 青い箱の中心から見て、スタート地点と正反対の方向にある点を「裏側」とする。
# 2. 箱を中心とする半径 1.0 m の円弧上の経由点をたどって回り込む（箱に直進するとぶつかるため）。
#    左回り・右回りのうち、他の箱から離れている方を選ぶ。
# 3. 裏側の点（箱から 1.0 m）に着いたら箱の方を向き、箱の中心から約 0.75 m まで前進する
#    （箱の半幅 0.15 m + 胴体前方 0.35 m = 0.5 m が接触距離なので、余裕を持たせる）。
# 4. 最後に向きを微調整して止まる。

def wrap(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def turn_to(target_yaw, tol=3.0, max_steps=150):
    # 目標の向きとの差が tol 以内になるまでその場で旋回する
    for _ in range(max_steps):
        err = wrap(target_yaw - get_yaw())
        if abs(err) < tol:
            return True
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)
    return False

def go_to(tx, ty, tol=0.12, max_steps=250):
    # 目標点の方向を向きながら前進する（向きのずれが大きいときはまず旋回）
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            return True
        heading = math.degrees(math.atan2(dy, dx))
        err = wrap(heading - get_yaw())
        if abs(err) > 30.0:
            turn_to(heading, tol=10.0, max_steps=60)
            continue
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        vx = clamp(0.8 * dist, 0.2, 0.6)
        walk(vx, 0.0, rate, duration=0.1)
    return False

def main():
    bx, by = get_object_position("blue_box")
    sx, sy = get_position()  # スタート地点

    # 箱から見たスタート地点の方向 [deg]。裏側はその反対（+180 deg）
    phi0 = math.degrees(math.atan2(sy - by, sx - bx))
    R = 1.0          # 回り込み時の箱からの距離
    D_FINAL = 0.75   # 最終的な箱中心からの距離

    def arc_points(sign):
        # 箱の周りを sign 方向に 45 deg 刻みで回り、裏側（+180 deg）まで到達する経由点
        pts = []
        for k in range(1, 5):
            a = math.radians(phi0 + sign * 45.0 * k)
            pts.append((bx + R * math.cos(a), by + R * math.sin(a)))
        return pts

    # 他の物体との最小距離が大きい方の回り方を選ぶ
    others = [o for o in get_objects() if o["name"] != "blue_box"]
    def clearance(pts):
        if not others:
            return float("inf")
        return min(math.hypot(px - o["x"], py - o["y"]) for (px, py) in pts for o in others)

    pts_ccw = arc_points(+1)
    pts_cw = arc_points(-1)
    waypoints = pts_ccw if clearance(pts_ccw) >= clearance(pts_cw) else pts_cw
    print("waypoints:", [(round(px, 2), round(py, 2)) for px, py in waypoints])

    # 円弧に沿って回り込む
    for (px, py) in waypoints:
        ok = go_to(px, py)
        x, y = get_position()
        print("reached" if ok else "timeout", "waypoint ->", (round(x, 2), round(y, 2)))

    # 箱の方を向く
    x, y = get_position()
    turn_to(math.degrees(math.atan2(by - y, bx - x)))

    # 箱の方を向いたまま、最終距離までゆっくり前進
    for _ in range(80):
        if distance_to(bx, by) <= D_FINAL:
            break
        x, y = get_position()
        err = wrap(math.degrees(math.atan2(by - y, bx - x)) - get_yaw())
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        walk(0.25, 0.0, rate, duration=0.1)

    # 向きを微調整して停止
    x, y = get_position()
    turn_to(math.degrees(math.atan2(by - y, bx - x)), tol=2.0)
    stop(1.0)

    x, y = get_position()
    print("final position:", (round(x, 2), round(y, 2)),
          "yaw:", round(get_yaw(), 1),
          "dist to blue_box:", round(distance_to(bx, by), 2))

main()
