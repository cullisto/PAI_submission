# 赤い箱の位置を取得し、箱の手前（中心から約0.6 m）まで向きを補正しながら前進する。
# 箱の中心には入れない（ぶつかる）ので、箱の大きさとロボットの体長を考慮して手前で止まる。
tx, ty = get_object_position("red_box")
STOP_DIST = 0.6  # 箱の中心からこの距離まで近づいたら停止（箱の半幅0.15 m + ロボット前方の余裕）

def angle_err(target_deg, current_deg):
    # -180〜180 に正規化した角度差 [deg]
    return (target_deg - current_deg + 180.0) % 360.0 - 180.0

def face_target(tol=5.0, max_steps=200):
    # 目標方向を向くまでその場で旋回する
    for _ in range(max_steps):
        x, y = get_position()
        bearing = math.degrees(math.atan2(ty - y, tx - x))
        err = angle_err(bearing, get_yaw())
        if abs(err) < tol:
            return
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

def go_to_red_box():
    face_target()
    for _ in range(600):  # 最大 60 秒
        x, y = get_position()
        dist = distance_to(tx, ty)
        if dist <= STOP_DIST:
            break
        bearing = math.degrees(math.atan2(ty - y, tx - x))
        err = angle_err(bearing, get_yaw())
        # 向きが大きくずれたら一度その場で向き直す
        if abs(err) > 30.0:
            face_target()
            continue
        # 残り距離に応じて減速しつつ、向きのずれを角速度で補正
        vx = max(0.2, min(0.6, 0.8 * (dist - STOP_DIST)))
        rate = max(-1.0, min(1.0, 1.5 * math.radians(err)))
        walk(vx, 0.0, rate, duration=0.1)
    stop(0.5)
    x, y = get_position()
    print("到着: 位置=(%.2f, %.2f), 赤い箱までの距離=%.2f m" % (x, y, distance_to(tx, ty)))

go_to_red_box()
