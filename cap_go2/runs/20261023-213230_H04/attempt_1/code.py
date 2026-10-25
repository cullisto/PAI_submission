# 方針:
#   赤い箱はコの字の奥の壁 (wall_back) の外側にあるため、まっすぐ前進すると
#   コの字の中に入り込み、奥の壁にぶつかってしまう。
#   そこで壁全体を囲む外接矩形を求め、右側 (-y 側) の外を回り込むルートを通る。
#     1) 右壁より外側 (-y 側) の点へ斜めに移動
#     2) 壁の外側を +x 方向に進み、奥の壁の向こう側まで出る
#     3) 赤い箱に向かい、手前 (約 0.55 m) で止まって箱の方を向く

SAFE_MARGIN = 0.65   # 壁との余裕 [m]（ロボットの胴体の大きさも考慮）
STOP_DIST = 0.55     # 箱の中心から止まる距離 [m]
DT = 0.1             # 制御周期 [s]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def angle_err_deg(target_deg):
    # 目標の向きと現在の向きの差を -180〜180 deg に正規化
    return (target_deg - get_yaw() + 180.0) % 360.0 - 180.0


def turn_to(target_deg, tol=4.0, max_steps=150):
    # その場で目標の向きまで旋回する
    for _ in range(max_steps):
        err = angle_err_deg(target_deg)
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=DT)


def go_to(tx, ty, tol=0.15, max_steps=400):
    # 点 (tx, ty) に向かって、向きを補正しながら前進する
    for _ in range(max_steps):
        x, y = get_position()
        dist = math.hypot(tx - x, ty - y)
        if dist < tol:
            return True
        target_heading = math.degrees(math.atan2(ty - y, tx - x))
        err = angle_err_deg(target_heading)
        if abs(err) > 30.0:
            # 向きが大きくずれているときはその場で旋回
            rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=DT)
        else:
            # 前進しながら向きを補正（近づいたら減速）
            vx = clamp(0.8 * dist, 0.2, 0.6)
            rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
            walk(vx, 0.0, rate, duration=DT)
    print("go_to: 時間切れ", (tx, ty))
    return False


def main():
    objects = get_objects()
    box_x, box_y = get_object_position("red_box")

    # 障害物（壁）全体の外接矩形を求める
    walls = [o for o in objects if o["is_obstacle"]]
    xmin = min(o["x"] - o["size_x"] / 2 for o in walls)
    xmax = max(o["x"] + o["size_x"] / 2 for o in walls)
    ymin = min(o["y"] - o["size_y"] / 2 for o in walls)
    print("壁の範囲: x[%.2f, %.2f] y[%.2f, ...]" % (xmin, xmax, ymin))

    # 右側 (-y 側) から回り込むための経由点
    detour_y = ymin - SAFE_MARGIN               # 右壁の外側のライン（約 -2.0）
    wp1 = (xmin - 1.0, detour_y)                # コの字の手前・右外側（約 (0.5, -2.0)）
    wp2 = (xmax + SAFE_MARGIN, detour_y)        # 奥の壁の向こう側・右外側（約 (3.8, -2.0)）

    for wp in (wp1, wp2):
        print("経由点へ移動:", wp)
        go_to(wp[0], wp[1], tol=0.15)
        print("  到着 位置:", get_position())

    # 赤い箱へ向かい、手前で止まる
    print("赤い箱へ接近")
    for _ in range(300):
        d = distance_to(box_x, box_y)
        if d <= STOP_DIST:
            break
        x, y = get_position()
        # 箱の中心から STOP_DIST 手前の点を目標にする
        ang = math.atan2(box_y - y, box_x - x)
        tx = box_x - STOP_DIST * math.cos(ang)
        ty = box_y - STOP_DIST * math.sin(ang)
        heading = math.degrees(ang)
        err = angle_err_deg(heading)
        if abs(err) > 30.0:
            rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=DT)
        else:
            rem = math.hypot(tx - x, ty - y)
            vx = clamp(0.8 * rem, 0.15, 0.5)
            rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
            walk(vx, 0.0, rate, duration=DT)

    # 最後に箱の方を向いて止まる
    x, y = get_position()
    turn_to(math.degrees(math.atan2(box_y - y, box_x - x)))
    stop(0.5)
    print("到着: 位置", get_position(), "向き %.1f deg" % get_yaw(),
          "箱までの距離 %.2f m" % distance_to(box_x, box_y))


main()
