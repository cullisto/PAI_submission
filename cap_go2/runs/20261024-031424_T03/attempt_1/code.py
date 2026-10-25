# 赤い箱の手前まで歩いて止まる。
# 箱の大きさは 0.3 m なので、正面から近づくと箱の中心から約 0.5 m で胴体が当たる。
# 少し余裕を持たせて、箱の中心から 0.6 m の位置で止まるようにする。

STOP_DIST = 0.6  # 箱の中心からの停止距離 [m]

bx, by = get_object_position("red_box")
print("red_box:", bx, by)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def yaw_error_to(tx, ty):
    # 目標点の方向と現在の向きの差 [deg]（-180〜180）
    x, y = get_position()
    target = math.degrees(math.atan2(ty - y, tx - x))
    return (target - get_yaw() + 180.0) % 360.0 - 180.0


def go_to_red_box():
    # 1) まず箱の方向を向く（今は正面にあるのでほぼ旋回不要）
    for _ in range(200):  # 最大 20 秒
        err = yaw_error_to(bx, by)
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

    # 2) 向きを補正しながら前進し、停止距離に達したら止まる
    for _ in range(600):  # 最大 60 秒
        d = distance_to(bx, by)
        if d <= STOP_DIST:
            break
        err = yaw_error_to(bx, by)
        rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
        # 残り距離に応じて減速（近づくほどゆっくり）
        v = clamp(0.8 * (d - STOP_DIST), 0.2, 0.8)
        # 向きが大きくずれているときは前進せず旋回を優先
        if abs(err) > 30.0:
            v = 0.0
        walk(v, 0.0, rate, duration=0.1)

    stop(0.5)
    x, y = get_position()
    print("到着: pos=(%.2f, %.2f), yaw=%.1f deg, 箱までの距離=%.2f m"
          % (x, y, get_yaw(), distance_to(bx, by)))


go_to_red_box()
