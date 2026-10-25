# 方針:
#   1) 青い箱 (blue_box) の手前まで近づく（箱の中心から約 0.6 m の位置で止まる）
#   2) そこから緑の箱 (green_box) の手前まで移動して止まる
#   - 箱の中心にはロボットが入れないので、中心から一定距離（APPROACH_DIST）で停止する
#   - 経路上に他の箱があれば、横に回り込む中継点を入れて避ける
#   - 目標方向へ旋回しながら前進するフィードバック制御で移動する

APPROACH_DIST = 0.6   # 箱の中心から止まる距離 [m]（箱の半幅 0.15 + ロボットの半身長 ≒ 0.35 + 余裕）
CLEARANCE = 0.6       # 経路上の他の箱から保つ距離 [m]


def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def turn_to(target_deg, tol=4.0, max_steps=150):
    # その場で target_deg の向きまで旋回する（最大 15 秒）
    for _ in range(max_steps):
        err = wrap_deg(target_deg - get_yaw())
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)


def seg_point_dist(ax, ay, bx, by, px, py):
    # 線分 A-B と点 P の最短距離と、線分上の最近点のパラメータ t を返す
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return math.hypot(px - ax, py - ay), 0.0
    t = clamp(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), t


def detour_waypoints(tx, ty, ignore_names):
    # 現在地から (tx, ty) への直線上に他の箱があれば、回り込む中継点を返す
    x, y = get_position()
    waypoints = []
    for obj in get_objects():
        if obj["name"] in ignore_names:
            continue
        ox, oy = obj["x"], obj["y"]
        d, t = seg_point_dist(x, y, tx, ty, ox, oy)
        if d < CLEARANCE and 0.0 < t < 1.0:
            # 進行方向に垂直な向きへ、箱から離れる側にずらした中継点を作る
            dx, dy = tx - x, ty - y
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            cx, cy = x + t * dx, y + t * dy
            side = 1.0 if (cx - ox) * nx + (cy - oy) * ny >= 0 else -1.0
            off = CLEARANCE + 0.2
            waypoints.append((t, ox + side * nx * off, oy + side * ny * off))
            print("回避:", obj["name"], "を避ける中継点を追加")
    waypoints.sort()
    return [(wx, wy) for _, wx, wy in waypoints]


def go_to(tx, ty, stop_dist, max_steps=400):
    # (tx, ty) から stop_dist の距離に入るまで、向きを合わせながら前進する（最大 40 秒）
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist <= stop_dist:
            return True
        desired = math.degrees(math.atan2(dy, dx))
        err = wrap_deg(desired - get_yaw())
        if abs(err) > 35.0:
            # 向きが大きくずれていればまずその場で旋回
            turn_to(desired)
            continue
        yaw_rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
        # 残り距離に応じて減速（0.2〜0.8 m/s）
        v = clamp(0.8 * (dist - stop_dist) + 0.2, 0.2, 0.8)
        walk(v, 0.0, yaw_rate, duration=0.1)
    print("警告: go_to の上限回数に達しました")
    return False


def approach_box(name):
    # 箱の手前まで（必要なら他の箱を回避しつつ）移動し、最後に箱の方を向く
    bx, by = get_object_position(name)
    for wx, wy in detour_waypoints(bx, by, ignore_names=[name]):
        go_to(wx, wy, stop_dist=0.15)
    go_to(bx, by, stop_dist=APPROACH_DIST)
    stop(0.3)
    x, y = get_position()
    turn_to(math.degrees(math.atan2(by - y, bx - x)))
    stop(0.3)
    print(name, "に到着: 位置", get_position(), "距離", round(distance_to(bx, by), 2), "m")


def main():
    # 1) 青い箱に寄る
    approach_box("blue_box")
    stop(0.5)
    # 2) 緑の箱まで行く
    approach_box("green_box")
    stop(1.0)


main()
