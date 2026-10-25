# 方針:
# - 旋回は一切しない（yaw_rate は常に 0）。前後(vx)と横歩き(vy)の速度だけで移動する。
# - ロボットは +x 方向を向いたまま。青い箱の「手前」は、ロボットから見て箱の手前側
#   (箱の -x 側) で、箱の正面を向いて立つ位置とする。
# - 箱の表面から前後方向に 0.35 m より近づけないので、箱の中心から
#   (箱の半幅 0.15 + 胴体の半長 0.35 + 余裕 0.1) = 0.6 m 手前を目標にする。
# - 途中に他の箱はない ((0,0) から (1.4,2.0) への直線上に障害物なし)。

def go_to_front_of_blue_box():
    # 青い箱の位置と大きさを取得
    bx, by = get_object_position("blue_box")
    size_x = 0.3
    for obj in get_objects():
        if obj["name"] == "blue_box":
            size_x = obj["size_x"]
            break

    yaw0 = get_yaw()
    yaw0_rad = math.radians(yaw0)

    # 目標点: ロボットの向き(前方)に沿って箱の手前側に下がった位置
    clearance = size_x / 2.0 + 0.35 + 0.1
    tx = bx - clearance * math.cos(yaw0_rad)
    ty = by - clearance * math.sin(yaw0_rad)
    print("start yaw: %.1f deg, target: (%.2f, %.2f)" % (yaw0, tx, ty))

    gain = 1.0
    tol = 0.05      # 到達とみなす距離 [m]
    min_speed = 0.12  # 目標付近で止まりきらないための最低速度 [m/s]

    for i in range(600):  # 最大 60 秒
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            break

        # ワールド座標の誤差をロボット座標系 (前=x, 左=y) に変換
        yaw = math.radians(get_yaw())
        ex = math.cos(yaw) * dx + math.sin(yaw) * dy
        ey = -math.sin(yaw) * dx + math.cos(yaw) * dy

        vx = gain * ex
        vy = gain * ey

        # 進行方向を保ったまま速度上限内に収める（比率を崩さずスケーリング）
        vx_lim = 1.0 if vx >= 0 else 0.5
        scale = 1.0
        if abs(vx) > vx_lim:
            scale = min(scale, vx_lim / abs(vx))
        if abs(vy) > 0.5:
            scale = min(scale, 0.5 / abs(vy))
        vx *= scale
        vy *= scale

        # 目標付近で速度が小さくなりすぎないようにする
        speed = math.hypot(vx, vy)
        if 0.0 < speed < min_speed:
            vx *= min_speed / speed
            vy *= min_speed / speed

        # 旋回はしない (yaw_rate = 0)
        walk(vx, vy, 0.0, duration=0.1)

        if i % 10 == 0:
            print("pos=(%.2f, %.2f) yaw=%.1f dist=%.2f" % (x, y, get_yaw(), dist))

    stop(1.0)
    x, y = get_position()
    print("final pos=(%.2f, %.2f) yaw=%.1f, distance to blue_box=%.2f"
          % (x, y, get_yaw(), distance_to(bx, by)))

go_to_front_of_blue_box()
