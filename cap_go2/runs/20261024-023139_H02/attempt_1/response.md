# 方針:
# 1. 4つの箱を回る順番を全通り（4! = 24 通り）試し、
#    スタート → 箱4つ → スタート の総距離が最短になる順番を選ぶ。
#    （各箱に寄る位置は箱の中心から一定距離手前なので、
#      箱の中心どうしの距離で比べれば順番の良し悪しは同じになる）
# 2. 各箱へは「現在位置から見た箱の手前 0.6 m」を目標に歩く。
#    斜めから近づくと箱の角（中心から約 0.21 m）に当たりやすいので、
#    0.35 m（胴体前半分）+ 0.21 m ≒ 0.56 m より少し余裕を取る。
# 3. 最後にスタート地点 (0, 0) に戻る。

start = get_position()

# 箱の一覧を取得（名前に "box" を含むもの）
boxes = []
for o in get_objects():
    if "box" in o["name"]:
        boxes.append((o["name"], o["x"], o["y"]))
print("箱:", boxes)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


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


# 最短の巡回順を探す
best_order = None
best_len = float("inf")
for order in permutations(boxes):
    total = 0.0
    prev = start
    for _, bx, by in order:
        total += dist(prev, (bx, by))
        prev = (bx, by)
    total += dist(prev, start)
    if total < best_len:
        best_len = total
        best_order = order

print("巡回順:", [b[0] for b in best_order], "中心間の総距離: %.2f m" % best_len)

APPROACH = 0.6  # 箱の中心から止まる距離 [m]


def visit_box(name, bx, by):
    x, y = get_position()
    d = math.hypot(bx - x, by - y)
    if d <= APPROACH + 0.05:
        print(name, "にはすでに十分近い")
        return True
    # 現在位置から箱へ向かう直線上で、箱の手前 APPROACH m の点を目標にする
    gx = bx - (bx - x) / d * APPROACH
    gy = by - (by - y) / d * APPROACH
    ok = move_to(gx, gy, tolerance=0.15, timeout=25.0)
    print(name, "に到着:", ok, "位置:", get_position())
    return ok


for name, bx, by in best_order:
    visit_box(name, bx, by)
    face(bx, by)  # 寄ったことが分かるよう箱の方を向く
    stop(0.3)

# スタート地点に戻る
ok = move_to(start[0], start[1], tolerance=0.15, timeout=25.0)
print("スタート地点に戻った:", ok, "位置:", get_position())
turn_to(0)  # 最初の向きに戻す
stop(0.5)
