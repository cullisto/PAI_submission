# 方針:
# 1. 4つの箱の位置を取得し、スタート地点を出発・帰着点とする巡回経路のうち
#    総距離が最短になる訪問順を全探索（4! = 24 通り）で求める。
# 2. その順に各箱の手前（箱の中心から 0.5 m、ロボット側）まで歩く。
#    箱の中心には入れないので、手前で止まることで「寄った」とみなす。
# 3. 最後にスタート地点へ戻り、最初の向き（0 deg）に戻して止まる。
# 参考: 中心間距離での最短順は 緑 → 赤 → 青 → 黄（またはその逆）で約 14.7 m。

STANDOFF = 0.5  # 箱の中心から手前で止まる距離 [m]

# スタート地点と最初の向きを記録
start_x, start_y = get_position()
start_yaw = get_yaw()

# 箱の一覧を取得（名前に "box" を含むもの）
boxes = []
for obj in get_objects():
    if "box" in obj["name"]:
        boxes.append((obj["name"], obj["x"], obj["y"]))
print("箱:", boxes)


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def permutations(items):
    # itertools が使えないので再帰で順列を作る
    if len(items) <= 1:
        return [list(items)]
    result = []
    for i in range(len(items)):
        rest = items[:i] + items[i + 1:]
        for p in permutations(rest):
            result.append([items[i]] + p)
    return result


def tour_length(order):
    pts = [(start_x, start_y)] + [(b[1], b[2]) for b in order] + [(start_x, start_y)]
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# 最短の巡回順を全探索で求める
best_order = None
best_len = float("inf")
for order in permutations(boxes):
    L = tour_length(order)
    if L < best_len:
        best_len = L
        best_order = order
print("訪問順:", [b[0] for b in best_order], "総距離(中心間): %.2f m" % best_len)


def approach_box(name, bx, by):
    # 現在位置から見て箱の手前 STANDOFF [m] の点を目標にして歩く
    x, y = get_position()
    d = math.hypot(bx - x, by - y)
    if d <= STANDOFF + 0.1:
        print(name, "にはすでに十分近い")
        return True
    gx = bx - (bx - x) / d * STANDOFF
    gy = by - (by - y) / d * STANDOFF
    # 距離に応じたタイムアウト（全体 120 秒に収まるよう控えめに）
    t = 5.0 + (d - STANDOFF) * 2.5
    reached = move_to(gx, gy, tolerance=0.15, timeout=t)
    print(name, "到着:", reached, "位置:", get_position(),
          "箱までの距離: %.2f m" % distance_to(bx, by))
    return reached


def main():
    for name, bx, by in best_order:
        approach_box(name, bx, by)
        stop(0.3)  # 寄ったことがわかるように一瞬止まる

    # スタート地点に戻る
    d = distance_to(start_x, start_y)
    reached = move_to(start_x, start_y, tolerance=0.1, timeout=5.0 + d * 2.5)
    print("スタート地点に帰着:", reached, "位置:", get_position())

    # 最初の向きに戻して静止
    turn_to(start_yaw)
    stop(0.5)


main()
