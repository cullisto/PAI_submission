# 方針:
#   紫の箱（危険物）の中心から 1.5 m 以内に入らずに赤い箱まで行く。
#   スタート (0,0) と赤い箱 (4.5,0) を結ぶ直線は紫の箱 (2.0,0.3) から 0.3 m しか離れていないため、
#   直進はできない。紫の箱を中心とする半径 R_WP (=2.0 m) の円周上に経由点を並べ、迂回する。
#     - 経由点どうしの角度間隔を 45 deg 以下にすると、経由点を結ぶ直線と紫の箱の距離は
#       R_WP * cos(22.5 deg) ≒ 1.85 m となり、1.5 m に対して十分な余裕がある。
#     - 紫の箱はスタート-ゴールの直線より +y 側（左）にあるので、反対の -y 側（右）を回る（近道）。
#   さらに歩行中は常に紫の箱との距離を監視し、1.7 m を切りそうなら横方向に押し戻す安全装置を入れる。
#   最後は赤い箱の手前 0.5 m で止まり、箱の方を向く。

HAZARD_LIMIT = 1.5   # 紫の箱の中心から入ってはいけない距離 [m]
R_WP = 2.0           # 経由点を置く円の半径 [m]
GUARD_DIST = 1.7     # この距離を切ったら押し戻す [m]
STOP_DIST = 0.5      # 赤い箱の中心から止まる距離 [m]
MAX_STEP_DEG = 40.0  # 経由点どうしの角度間隔の上限 [deg]
DT = 0.1             # 制御周期 [s]

min_hazard_dist = [1e9]  # 実行中に記録した紫の箱との最小距離


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def angle_err_deg(target_deg):
    return wrap_deg(target_deg - get_yaw())


def seg_point_dist(ax, ay, bx, by, px, py):
    # 線分 AB と点 P の最短距離
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return math.hypot(px - ax, py - ay)
    t = clamp(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def safe_walk(vx, yaw_rate, hx, hy):
    # 紫の箱との距離を監視しながら walk する
    x, y = get_position()
    d = math.hypot(x - hx, y - hy)
    min_hazard_dist[0] = min(min_hazard_dist[0], d)
    vy = 0.0
    if d < GUARD_DIST:
        # 紫の箱から離れる方向（ワールド座標）をロボット座標に変換
        ax, ay = (x - hx) / d, (y - hy) / d
        yaw = math.radians(get_yaw())
        away_fwd = ax * math.cos(yaw) + ay * math.sin(yaw)
        away_left = -ax * math.sin(yaw) + ay * math.cos(yaw)
        gain = clamp((GUARD_DIST - d) / 0.2, 0.0, 1.0)
        vy = 0.4 * gain * away_left
        # 箱に近づく向きに進んでいるなら前進速度を落とす
        if away_fwd < 0.0:
            vx = vx * (1.0 - gain)
        print("警告: 紫の箱まで %.2f m → 押し戻し" % d)
    walk(vx, vy, yaw_rate, duration=DT)


def turn_to(target_deg, hx, hy, tol=4.0, max_steps=150):
    for _ in range(max_steps):
        err = angle_err_deg(target_deg)
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        safe_walk(0.0, rate, hx, hy)


def go_to(tx, ty, hx, hy, tol=0.15, max_steps=400):
    for _ in range(max_steps):
        x, y = get_position()
        dist = math.hypot(tx - x, ty - y)
        if dist < tol:
            return True
        heading = math.degrees(math.atan2(ty - y, tx - x))
        err = angle_err_deg(heading)
        if abs(err) > 25.0:
            # 向きが大きくずれていればその場で旋回（コースを外れないように）
            rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            safe_walk(0.0, rate, hx, hy)
        else:
            vx = clamp(0.8 * dist, 0.15, 0.5)
            rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
            safe_walk(vx, rate, hx, hy)
    print("go_to: 時間切れ", (tx, ty))
    return False


def main():
    hx, hy = get_object_position("purple_box")
    gx_box, gy_box = get_object_position("red_box")
    sx, sy = get_position()

    # 停止目標: 赤い箱の手前 STOP_DIST（紫の箱から遠ざかる側から近づく）
    ux, uy = gx_box - hx, gy_box - hy
    n = math.hypot(ux, uy)
    gx = gx_box - STOP_DIST * ux / n
    gy = gy_box - STOP_DIST * uy / n
    print("停止目標: (%.2f, %.2f) 紫の箱まで %.2f m" % (gx, gy, math.hypot(gx - hx, gy - hy)))

    waypoints = []
    if seg_point_dist(sx, sy, gx, gy, hx, hy) > HAZARD_LIMIT + 0.3:
        print("直進しても安全")
    else:
        # 紫の箱がスタート→ゴール直線のどちら側にあるか（外積）で回る側を決める
        cross = (gx - sx) * (hy - sy) - (gy - sy) * (hx - sx)
        # cross > 0: 紫の箱は左側 → 右側（時計回りではなく、箱から見て角度が増える向き…を計算で決定）
        a_start = math.degrees(math.atan2(sy - hy, sx - hx))
        a_goal = math.degrees(math.atan2(gy - hy, gx - hx))
        ccw = wrap_deg(a_goal - a_start) % 360.0     # 反時計回りに回る角度
        cw = ccw - 360.0                               # 時計回りに回る角度（負）
        # 箱から見て反時計回りに回ると、箱の右側(ロボット進行方向から見て)を通るかを判定:
        # 経路の中間点が直線のどちら側にあるかで選ぶ
        def mid_side(delta):
            am = math.radians(a_start + delta / 2.0)
            mx, my = hx + R_WP * math.cos(am), hy + R_WP * math.sin(am)
            return (gx - sx) * (my - sy) - (gy - sy) * (mx - sx)
        # 箱と反対側を通るルートを選ぶ
        sweep = ccw if mid_side(ccw) * cross < 0 else cw
        steps = max(2, int(math.ceil(abs(sweep) / MAX_STEP_DEG)))
        for i in range(1, steps):
            a = math.radians(a_start + sweep * i / steps)
            waypoints.append((hx + R_WP * math.cos(a), hy + R_WP * math.sin(a)))
        print("迂回角度 %.1f deg, 経由点 %d 個" % (sweep, len(waypoints)))

    # 念のため全区間の安全性をチェック
    path = [(sx, sy)] + waypoints + [(gx, gy)]
    for i in range(len(path) - 1):
        d = seg_point_dist(path[i][0], path[i][1], path[i + 1][0], path[i + 1][1], hx, hy)
        print("区間 %d: 紫の箱との最短距離 %.2f m" % (i, d))

    for wp in waypoints:
        print("経由点へ:", (round(wp[0], 2), round(wp[1], 2)))
        go_to(wp[0], wp[1], hx, hy, tol=0.2)

    print("赤い箱の手前へ")
    go_to(gx, gy, hx, hy, tol=0.1)

    # 赤い箱の方を向いて停止
    x, y = get_position()
    turn_to(math.degrees(math.atan2(gy_box - y, gx_box - x)), hx, hy)
    stop(0.5)
    print("到着: 位置", get_position(), "赤い箱まで %.2f m" % distance_to(gx_box, gy_box))
    print("紫の箱との最小距離: %.2f m" % min_hazard_dist[0])


main()
