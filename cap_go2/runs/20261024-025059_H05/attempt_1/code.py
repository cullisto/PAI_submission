# 方針:
#  紫の箱 (2.0, 0.3) は、スタート (0,0) と赤い箱 (4.5, 0) を結ぶ直線のすぐ近く (左 0.3 m) にある。
#  1.5 m 以内に入らないよう、紫の箱から遠い側 (右側 = y が負の側) に大きく回り込む。
#  安全マージンをとり、経路上の各点・各区間が紫の箱の中心から 1.8 m 以上離れるように中継点を置く。
#  さらに歩行中も短い区切りで位置を確認し、近づきすぎたら紫の箱から離れる方向へ退避する。

SAFE_R = 1.5        # 指示された禁止半径 [m]
MARGIN_R = 1.8      # 経路計画で確保する距離 [m]
APPROACH = 0.55     # 赤い箱の中心から止まる距離 [m]（胴体前半 0.35 + 箱の半分 0.15 + 余裕）

px, py = get_object_position("purple_box")
rx, ry = get_object_position("red_box")
sx, sy = get_position()


def dist_point_segment(qx, qy, ax, ay, bx, by):
    """点 q と線分 ab の最短距離"""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return math.hypot(qx - ax, qy - ay)
    t = ((qx - ax) * dx + (qy - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(qx - cx, qy - cy)


# 紫の箱がスタート→赤い箱の直線のどちら側にあるかを調べ、反対側を回る
cross = (rx - sx) * (py - sy) - (ry - sy) * (px - sx)
side = -1.0 if cross > 0 else 1.0   # 紫が左側なら右側 (y 負) を通る
side_y = py + side * 2.0            # 紫の箱から 2.0 m 横のライン

waypoints = [
    (px - 1.5, side_y),
    (px, side_y),
    (px + 1.5, side_y),
]

# 最終目標: 最後の中継点から赤い箱へ向かう方向で、箱の手前 APPROACH m の点
lx, ly = waypoints[-1]
d = math.hypot(rx - lx, ry - ly)
gx = rx - (rx - lx) / d * APPROACH
gy = ry - (ry - ly) / d * APPROACH
waypoints.append((gx, gy))

# 経路全体のクリアランスを確認（ログ用）
prev = (sx, sy)
for wx, wy in waypoints:
    c = dist_point_segment(px, py, prev[0], prev[1], wx, wy)
    print("区間", prev, "->", (round(wx, 2), round(wy, 2)), "紫との最小距離:", round(c, 2))
    prev = (wx, wy)


def escape_from_purple():
    """紫の箱に近づきすぎたとき、紫の箱から離れる方向へ退避する"""
    x, y = get_position()
    dd = math.hypot(x - px, y - py)
    if dd < 1e-6:
        return
    ex = px + (x - px) / dd * (MARGIN_R + 0.1)
    ey = py + (y - py) / dd * (MARGIN_R + 0.1)
    print("紫の箱に近すぎる (距離 %.2f m)。退避します" % dd)
    move_to(ex, ey, tolerance=0.15, timeout=5.0)


def go_safely(wx, wy, tol):
    """短い区切りで move_to を繰り返し、毎回紫の箱との距離を確認する"""
    for _ in range(40):  # 回数上限
        x, y = get_position()
        if math.hypot(wx - x, wy - y) <= tol:
            return True
        if distance_to(px, py) < SAFE_R + 0.15:
            escape_from_purple()
        if move_to(wx, wy, tolerance=tol, timeout=1.0):
            return True
    return False


for i, (wx, wy) in enumerate(waypoints):
    last = (i == len(waypoints) - 1)
    ok = go_safely(wx, wy, 0.1 if last else 0.2)
    x, y = get_position()
    print("中継点 %d (%.2f, %.2f) 到着: %s, 現在位置 (%.2f, %.2f), 紫との距離 %.2f m"
          % (i, wx, wy, ok, x, y, distance_to(px, py)))

# 赤い箱の方を向いて停止
face(rx, ry)
stop(0.5)
x, y = get_position()
print("最終位置 (%.2f, %.2f), 赤い箱まで %.2f m, 紫の箱まで %.2f m"
      % (x, y, distance_to(rx, ry), distance_to(px, py)))
