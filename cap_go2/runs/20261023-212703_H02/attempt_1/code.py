# 方針:
# 1. get_objects() で箱の位置を取得し、全順列（4! = 24 通り）を総当たりして
#    「スタート → 全箱 → スタート」の総距離が最短になる巡回順を求める。
# 2. 各区間の直線が他の箱に近すぎる場合は、箱を避ける経由点を 1 つ挟む。
# 3. 各箱へは、ぶつからないよう中心から APPROACH_DIST [m] の位置まで近づいて少し止まる。
# 4. 最後にスタート地点へ戻り、開始時の向きに戻して停止する。

APPROACH_DIST = 0.6   # 箱の中心からこの距離で「寄った」とみなす（Go2 の胴体前端 ~0.35 m + 箱の半幅 0.15 m + 余裕）
CLEARANCE = 0.6       # 移動中に他の箱の中心から最低限とりたい距離
DT = 0.1              # 制御周期 [s]
MAX_SPEED = 0.8       # 前進速度の上限 [m/s]


def wrap_rad(a):
    # 角度を -pi〜pi に正規化
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def permutations(items):
    # itertools が使えないので再帰で順列を生成
    if len(items) <= 1:
        return [list(items)]
    result = []
    for i in range(len(items)):
        for rest in permutations(items[:i] + items[i + 1:]):
            result.append([items[i]] + rest)
    return result


def point_segment_dist(px, py, ax, ay, bx, by):
    # 点 P と線分 AB の最短距離と、最近点を返す
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else clamp(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), (cx, cy)


def leg_waypoints(p, q, boxes, exclude):
    # p → q の直線が他の箱に近すぎる場合、箱を横に避ける経由点を 1 つ追加する
    for name, (bx, by) in boxes.items():
        if name in exclude:
            continue
        d, (cx, cy) = point_segment_dist(bx, by, p[0], p[1], q[0], q[1])
        if d < CLEARANCE:
            # 線分に垂直な方向で、最近点のある側へ箱から離れた経由点を置く
            sx, sy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(sx, sy) or 1.0
            nx, ny = -sy / L, sx / L
            if (cx - bx) * nx + (cy - by) * ny < 0:
                nx, ny = -nx, -ny
            off = CLEARANCE + 0.2
            return [(bx + nx * off, by + ny * off), q]
    return [q]


def path_length(points):
    return sum(math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
               for i in range(len(points) - 1))


def tour_cost(order, start, boxes):
    # 巡回順 order の総距離（回避経由点込み、箱の中心で近似）
    pts = [start]
    prev = start
    names = list(order) + [None]
    for name in names:
        target = boxes[name] if name is not None else start
        excl = {name} if name is not None else set()
        wps = leg_waypoints(prev, target, boxes, excl)
        pts.extend(wps)
        prev = target
    return path_length(pts)


def go_to(tx, ty, stop_dist, max_steps=400):
    # (tx, ty) との距離が stop_dist 以下になるまで、向きを合わせながら歩く
    for _ in range(max_steps):
        x, y = get_position()
        d = math.hypot(tx - x, ty - y)
        if d <= stop_dist:
            return True
        yaw = math.radians(get_yaw())
        err = wrap_rad(math.atan2(ty - y, tx - x) - yaw)
        yaw_rate = clamp(1.5 * err, -1.0, 1.0)
        if abs(err) > 0.6:
            vx = 0.0  # 向きが大きくずれているときはその場で旋回
        else:
            # 目標が近づいたら減速、向きのずれに応じて前進速度を落とす
            vx = clamp(0.8 * (d - stop_dist) + 0.15, 0.15, MAX_SPEED) * math.cos(err)
        walk(vx, 0.0, yaw_rate, duration=DT)
    print("go_to: 上限ステップに到達", (tx, ty))
    return False


def turn_to(target_deg, max_steps=150):
    # 指定した向き [deg] になるまでその場で旋回する
    for _ in range(max_steps):
        err = (target_deg - get_yaw() + 180.0) % 360.0 - 180.0
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=DT)


def main():
    start = get_position()
    start_yaw = get_yaw()

    # 箱の一覧を取得
    boxes = {}
    for obj in get_objects():
        if "box" in obj["name"]:
            boxes[obj["name"]] = (obj["x"], obj["y"])
    print("箱:", boxes)

    # 最短の巡回順を総当たりで探索
    best_order, best_cost = None, float("inf")
    for order in permutations(list(boxes.keys())):
        c = tour_cost(order, start, boxes)
        if c < best_cost:
            best_order, best_cost = order, c
    print("巡回順:", best_order, "概算距離: %.2f m" % best_cost)

    # 順に各箱へ寄る
    for name in best_order:
        bx, by = boxes[name]
        wps = leg_waypoints(get_position(), (bx, by), boxes, {name})
        for wx, wy in wps[:-1]:          # 回避用の経由点は通過するだけ
            go_to(wx, wy, 0.25)
        go_to(bx, by, APPROACH_DIST)     # 箱の手前で止まる
        stop(0.5)
        print("到着:", name, "位置:", get_position(), "距離: %.2f m" % distance_to(bx, by))

    # スタート地点へ戻る
    wps = leg_waypoints(get_position(), start, boxes, set())
    for wx, wy in wps[:-1]:
        go_to(wx, wy, 0.25)
    go_to(start[0], start[1], 0.1)
    stop(0.3)
    turn_to(start_yaw)                   # 開始時の向きに戻す
    stop(1.0)
    print("帰還:", get_position(), "向き: %.1f deg" % get_yaw())


main()
