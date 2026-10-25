# 方針:
#   1. スタート地点から青い箱へ向かう方向ベクトル u を求め、
#      「裏側」の目標点 = 箱の中心 + u * 1.0 m とする（箱の向こう側）。
#   2. 箱に直接突っ込まないよう、箱の横（u に垂直な方向）に経由点を置き、
#      経由点 → 目標点 の順に移動して回り込む。
#   3. 最後に青い箱の方を向いて静止する。

STANDOFF = 1.0  # 箱の中心から目標点・経由点までの距離 [m]（箱の半幅 0.15 m + ロボットの体格を考慮して余裕を取る）


def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0


def turn_to(target_yaw, tol=3.0, max_steps=200):
    # 目標の向き target_yaw [deg] までその場で旋回する
    for _ in range(max_steps):
        err = wrap_deg(target_yaw - get_yaw())
        if abs(err) < tol:
            break
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)


def go_to(tx, ty, tol=0.1, max_steps=400):
    # 点 (tx, ty) へ向きを合わせながら前進する（最大 40 秒）
    for _ in range(max_steps):
        x, y = get_position()
        dist = math.hypot(tx - x, ty - y)
        if dist < tol:
            break
        desired = math.degrees(math.atan2(ty - y, tx - x))
        err = wrap_deg(desired - get_yaw())
        if abs(err) > 25.0:
            # 向きが大きくずれているときはその場で旋回
            rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=0.1)
        else:
            # 前進しながら向きを補正。近づいたら減速
            vx = max(0.2, min(0.6, 0.8 * dist))
            rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
            walk(vx, 0.0, rate, duration=0.1)
    print("reached", (tx, ty), "pos:", get_position())


def main():
    sx, sy = get_position()                       # スタート地点
    bx, by = get_object_position("blue_box")      # 青い箱の中心

    # スタート地点 → 箱 の単位ベクトル u
    dx, dy = bx - sx, by - sy
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    # u に垂直な単位ベクトル（左側）n
    nx, ny = -uy, ux

    # 裏側の目標点（スタート地点から見て箱の反対側）
    goal_x, goal_y = bx + ux * STANDOFF, by + uy * STANDOFF
    # 回り込み用の経由点（箱の横）
    via_x, via_y = bx + nx * STANDOFF, by + ny * STANDOFF
    print("via:", (via_x, via_y), "goal:", (goal_x, goal_y))

    # 経由点を通って裏側へ回り込む
    go_to(via_x, via_y, tol=0.15)
    go_to(goal_x, goal_y, tol=0.08)
    stop(0.3)

    # 青い箱の方を向く
    x, y = get_position()
    face = math.degrees(math.atan2(by - y, bx - x))
    turn_to(face)
    stop(1.0)
    print("final pos:", get_position(), "yaw:", get_yaw(),
          "dist to blue_box:", distance_to(bx, by))


main()
