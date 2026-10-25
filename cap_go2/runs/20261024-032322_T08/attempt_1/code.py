# 赤い箱と青い箱のちょうど中間の地点へ移動する
# 中間点は (3.0+2.0)/2, (0.0+2.0)/2 = (2.5, 1.0) の予定。各箱の中心から約 1.1 m 離れているので衝突しない。
# 現在地 (0,0) からの直線経路も箱から十分離れている。

def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def go_to_midpoint():
    # 箱の位置は API から取得して中間点を計算する
    rx, ry = get_object_position("red_box")
    bx, by = get_object_position("blue_box")
    tx, ty = (rx + bx) / 2.0, (ry + by) / 2.0
    print("目標地点:", tx, ty)

    # --- 1. その場で目標方向を向く ---
    for _ in range(200):  # 最大 20 秒
        x, y = get_position()
        target_yaw = math.degrees(math.atan2(ty - y, tx - x))
        err = wrap_deg(target_yaw - get_yaw())
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

    # --- 2. 向きを補正しながら前進し、近づいたら横移動も使って微調整 ---
    for _ in range(600):  # 最大 60 秒
        x, y = get_position()
        d = distance_to(tx, ty)
        if d < 0.05:
            break
        yaw = get_yaw()
        if d < 0.3:
            # 微調整: 目標までのベクトルをロボット座標系に変換して全方向移動
            dx, dy = tx - x, ty - y
            c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            fx = c * dx + s * dy       # 前方向成分
            fy = -s * dx + c * dy      # 左方向成分
            v = clamp(1.5 * d, 0.1, 0.3)
            walk(v * fx / d, v * fy / d, 0.0, duration=0.1)
        else:
            # 巡航: 目標方向に向きを合わせながら前進（近づくほど減速）
            target_yaw = math.degrees(math.atan2(ty - y, tx - x))
            err = wrap_deg(target_yaw - yaw)
            rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
            if abs(err) > 30.0:
                vx = 0.0  # 向きが大きくずれていたら旋回を優先
            else:
                vx = min(0.8, 0.8 * d + 0.1) * math.cos(math.radians(err))
            walk(vx, 0.0, rate, duration=0.1)

    stop(0.5)
    x, y = get_position()
    print("到着位置:", round(x, 3), round(y, 3), "目標までの距離:", round(distance_to(tx, ty), 3))

go_to_midpoint()
