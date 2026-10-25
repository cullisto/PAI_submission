# 方針:
#  紫の箱(危険物)の中心から 1.5 m 以内に入らないよう、紫の箱を中心とした
#  半径 R = 1.5 + 余裕 0.6 = 2.1 m の円弧に沿って迂回し、赤い箱の手前まで行く。
#  move_to は障害物を避けず直進するので、円弧を細かい経由点に分割して
#  弦(直線区間)が円の内側に食い込みすぎないようにする。
#  (半径 2.1 m、刻み 15 度なら弦の最接近距離は 2.1*cos(7.5°) ≈ 2.08 m)

SAFE_R = 1.5          # 守るべき距離 [m]
MARGIN = 0.6          # 歩行の誤差や経由点の切り替えに対する余裕 [m]
R = SAFE_R + MARGIN   # 迂回する円弧の半径 [m]
STEP_DEG = 15.0       # 円弧上の経由点の角度刻み [deg]
STOP_BEFORE = 0.5     # 赤い箱の中心からこれだけ手前で止まる [m]

px, py = get_object_position("purple_box")
rx, ry = get_object_position("red_box")
sx, sy = get_position()

min_dist = [distance_to(px, py)]  # 確認用: 紫の箱への最小距離の記録


def check(label):
    d = distance_to(px, py)
    if d < min_dist[0]:
        min_dist[0] = d
    print(label, "位置:", get_position(), "紫の箱までの距離: %.2f m" % d)


def seg_min_dist(ax, ay, bx, by, cx, cy):
    # 線分 AB と点 C の最短距離
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(cx - ax, cy - ay)
    t = ((cx - ax) * dx + (cy - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    return math.hypot(ax + t * dx - cx, ay + t * dy - cy)


def go(x, y, label):
    ok = move_to(x, y, tolerance=0.15, timeout=15.0)
    check(label + (" 到着" if ok else " 時間切れ"))
    return ok


def main():
    check("開始")

    # もし開始時点で既に近すぎる場合は、紫の箱から離れる方向へ退避する
    d0 = distance_to(px, py)
    if d0 < R:
        ux, uy = (sx - px) / d0, (sy - py) / d0
        go(px + ux * R, py + uy * R, "退避")

    cx, cy = get_position()

    # ゴール地点: 現在地から赤い箱へ向かう直線上で、箱の中心の STOP_BEFORE m 手前
    dg = math.hypot(rx - cx, ry - cy)
    gx = rx - (rx - cx) / dg * STOP_BEFORE
    gy = ry - (ry - cy) / dg * STOP_BEFORE

    # 直進しても安全ならそのまま行く
    if seg_min_dist(cx, cy, gx, gy, px, py) >= R:
        go(gx, gy, "ゴール")
    else:
        # 紫の箱が進行方向の左右どちらにあるか(外積の符号)で迂回する側を決める
        # 左にあれば右側を通る = 紫の箱の周りを反時計回り(角度増加)に回る
        cross = (gx - cx) * (py - cy) - (gy - cy) * (px - cx)
        a_start = math.atan2(cy - py, cx - px)
        a_goal = math.atan2(gy - py, gx - px)
        delta = a_goal - a_start
        if cross >= 0:
            while delta <= 0:
                delta += 2 * math.pi   # 反時計回り
        else:
            while delta >= 0:
                delta -= 2 * math.pi   # 時計回り

        n = max(2, int(math.ceil(abs(math.degrees(delta)) / STEP_DEG)))
        # 端点(i=0, i=n)は除き、円弧上の中間経由点だけを順にたどる
        for i in range(1, n):
            a = a_start + delta * i / n
            wx = px + R * math.cos(a)
            wy = py + R * math.sin(a)
            go(wx, wy, "経由点 %d/%d" % (i, n - 1))

        go(gx, gy, "ゴール")

    # 最後に赤い箱の方を向いて静止
    face(rx, ry)
    stop(0.5)
    check("終了")
    print("赤い箱までの距離: %.2f m" % distance_to(rx, ry))
    print("紫の箱への最小距離(各経由点で計測): %.2f m (制約 %.1f m)" % (min_dist[0], SAFE_R))


main()
