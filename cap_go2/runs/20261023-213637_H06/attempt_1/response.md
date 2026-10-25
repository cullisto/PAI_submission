# 方針:
#   1. 赤い箱の中心から見て「ロボットの現在位置の方向」に 1.0 m 離れた点を目標地点にする
#      （初期位置 (0,0)、箱 (3,0) なら目標は (2.0, 0.0)）
#   2. 目標地点まで前進で移動する（進行方向へ旋回しながら歩く）
#   3. 箱と反対方向を向くように旋回し、お尻（後ろ側）を箱に向ける
#      （目標の向き = 箱からロボットへ向かう方向。今回は 180 deg）
#   4. 向きを保ったまま横・前後移動で位置を微調整し、最後に向きを再調整して止まる

BOX_NAME = "red_box"
STANDOFF = 1.0  # 箱の中心からの距離 [m]


def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def turn_to(target_deg, tol=2.0, max_steps=200):
    # その場で target_deg の向きになるまで旋回する（最大 max_steps*0.1 秒）
    for _ in range(max_steps):
        err = wrap_deg(target_deg - get_yaw())
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.25:
            rate = math.copysign(0.25, rate)
        walk(0.0, 0.0, rate, duration=0.1)


def go_to(tx, ty, tol=0.05, hold_yaw=None, vmax=0.6, max_steps=400):
    # 目標点 (tx, ty) まで歩く。
    # hold_yaw が None なら進行方向へ向きを合わせながら歩き、
    # 指定されていればその向きを保ったまま（横・後ろ歩きも使って）移動する。
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            break
        yaw_deg = get_yaw()
        yaw = math.radians(yaw_deg)
        # ワールド座標の差分をロボット座標系へ変換
        bx = math.cos(yaw) * dx + math.sin(yaw) * dy
        by = -math.sin(yaw) * dx + math.cos(yaw) * dy

        # 目標に近づくほど減速（ただし止まりきらないよう下限あり）
        v = clamp(1.0 * dist, 0.1, vmax)
        vx = v * bx / dist
        vy = v * by / dist

        # 向きの制御
        if hold_yaw is None:
            if dist > 0.3:
                yaw_err = wrap_deg(math.degrees(math.atan2(dy, dx)) - yaw_deg)
            else:
                yaw_err = 0.0  # 目標直前では向きを変えない
            # 進行方向と大きくずれているときは前進を抑えて旋回を優先
            if abs(yaw_err) > 45.0:
                vx, vy = 0.0, 0.0
        else:
            yaw_err = wrap_deg(hold_yaw - yaw_deg)
        yaw_rate = clamp(1.5 * math.radians(yaw_err), -1.0, 1.0)

        walk(clamp(vx, -0.5, 1.0), clamp(vy, -0.5, 0.5), yaw_rate, duration=0.1)


def main():
    bx, by = get_object_position(BOX_NAME)
    rx, ry = get_position()

    # 箱からロボットへ向かう単位ベクトル（重なっている場合は -x 方向を使う）
    vx, vy = rx - bx, ry - by
    d = math.hypot(vx, vy)
    if d < 1e-6:
        vx, vy, d = -1.0, 0.0, 1.0
    ux, uy = vx / d, vy / d

    # 目標地点と、お尻を箱に向けるための向き（箱と反対方向を向く）
    tx, ty = bx + STANDOFF * ux, by + STANDOFF * uy
    target_yaw = math.degrees(math.atan2(uy, ux))
    print("target point: (%.2f, %.2f), target yaw: %.1f deg" % (tx, ty, target_yaw))

    # 2. 目標地点まで前進で移動
    go_to(tx, ty, tol=0.08)
    stop(0.3)

    # 3. 箱と反対方向を向く（お尻が箱側になる）
    turn_to(target_yaw)
    stop(0.3)

    # 4. 向きを保ったまま位置を微調整し、最後に向きを再確認
    go_to(tx, ty, tol=0.03, hold_yaw=target_yaw, vmax=0.3, max_steps=150)
    turn_to(target_yaw, tol=1.5)
    stop(1.0)

    # 結果の確認
    x, y = get_position()
    yaw = get_yaw()
    to_box = math.degrees(math.atan2(by - y, bx - x))
    print("final pos: (%.2f, %.2f), yaw: %.1f deg" % (x, y, yaw))
    print("distance to box: %.2f m" % distance_to(bx, by))
    print("rear-to-box angle error: %.1f deg" % wrap_deg(yaw + 180.0 - to_box))


main()
