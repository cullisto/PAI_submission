# 方針:
# 1) 4つの箱の巡回順を全順列（4! = 24通り）で比べ、スタート→箱×4→スタートの総距離が最短の順番を選ぶ
#    （中心間距離で評価。この配置では 黄→青→赤→緑 またはその逆、約14.7 m が最短）
# 2) 各箱へは「現在位置から箱中心へ向かう直線上で、箱中心から 0.65 m 手前」の点を目標にして近づく
#    （正面から近づくと箱中心から約 0.5 m で胴体が当たるので、少し余裕を持たせる）
# 3) 最後にスタート地点へ戻り、開始時の向きに合わせて停止する

SIM_LIMIT = 110.0      # 安全側のシミュレーション時間上限 [s]
DT = 0.1               # 1ステップの指令時間 [s]
elapsed = [0.0]        # 経過時間（walk/stop で加算）


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def do_walk(vx, vy, wz, dt=DT):
    walk(vx, vy, wz, duration=dt)
    elapsed[0] += dt


def do_stop(dt):
    stop(dt)
    elapsed[0] += dt


def go_to(tx, ty, tol, center=None, near_dist=None, max_steps=500):
    """点 (tx, ty) へ向きを合わせながら前進する。
    center/near_dist を与えた場合、その点まで near_dist 以内に入っても到着とみなす。"""
    for _ in range(max_steps):
        if elapsed[0] > SIM_LIMIT:
            print("時間上限に近いため移動を打ち切り")
            return False
        x, y = get_position()
        dx, dy = tx - x, ty - y
        d = math.hypot(dx, dy)
        if d < tol:
            return True
        if center is not None and distance_to(center[0], center[1]) <= near_dist:
            return True
        err = wrap_deg(math.degrees(math.atan2(dy, dx)) - get_yaw())
        wz = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(err) > 35.0:
            # 向きが大きくずれているときはその場で旋回
            if abs(wz) < 0.3:
                wz = math.copysign(0.3, wz)
            vx = 0.0
        else:
            # 遠いときは速く、近づいたら減速。向きのずれに応じて前進量を減らす
            vx = clamp(1.0 * d, 0.2, 0.8) * math.cos(math.radians(err))
        do_walk(vx, 0.0, wz)
    return False


def turn_to(target_yaw, max_steps=200):
    for _ in range(max_steps):
        if elapsed[0] > SIM_LIMIT:
            return
        err = wrap_deg(target_yaw - get_yaw())
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        do_walk(0.0, 0.0, rate)


def permutations(items):
    if len(items) <= 1:
        return [list(items)]
    result = []
    for i in range(len(items)):
        rest = items[:i] + items[i + 1:]
        for p in permutations(rest):
            result.append([items[i]] + p)
    return result


def main():
    start = get_position()
    start_yaw = get_yaw()

    # シーン内の箱を取得
    boxes = []
    for o in get_objects():
        if "box" in o["name"]:
            half = max(o["size_x"], o["size_y"]) / 2.0
            boxes.append((o["name"], o["x"], o["y"], half))
    print("箱:", [b[0] for b in boxes])

    # 最短の巡回順を全探索
    best_order, best_len = None, float("inf")
    for order in permutations(boxes):
        px, py = start
        total = 0.0
        for _, bx, by, _ in order:
            total += math.hypot(bx - px, by - py)
            px, py = bx, by
        total += math.hypot(start[0] - px, start[1] - py)
        if total < best_len:
            best_len, best_order = total, order
    print("巡回順:", [b[0] for b in best_order], "推定距離(中心間): %.2f m" % best_len)

    # 順番に箱へ寄る
    for name, bx, by, half in best_order:
        x, y = get_position()
        D = math.hypot(bx - x, by - y)
        approach = half + 0.35 + 0.15      # 箱表面 + 胴体の前半分 + 余裕 = 0.65 m
        if D > approach:
            ux, uy = (bx - x) / D, (by - y) / D
            tx, ty = bx - ux * approach, by - uy * approach
            go_to(tx, ty, tol=0.1, center=(bx, by), near_dist=approach + 0.05)
        do_stop(0.3)
        px, py = get_position()
        print("%s に到着: 位置(%.2f, %.2f) 箱までの距離 %.2f m, 経過 %.1f s"
              % (name, px, py, distance_to(bx, by), elapsed[0]))

    # スタート地点へ戻る
    go_to(start[0], start[1], tol=0.08)
    turn_to(start_yaw)
    do_stop(0.5)
    px, py = get_position()
    print("スタート地点に帰還: 位置(%.2f, %.2f) 向き %.1f deg, 経過 %.1f s"
          % (px, py, get_yaw(), elapsed[0]))


main()
