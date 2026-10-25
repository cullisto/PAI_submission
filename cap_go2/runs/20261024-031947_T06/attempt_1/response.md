# 一番近い箱を選び、その箱の方を向いてから、ぶつからない手前の位置まで近づいて止まる

def go_to_nearest_box():
    # --- 1. 一番近い箱を探す ---
    objs = get_objects()
    boxes = [o for o in objs
             if "box" in o["name"].lower() or "箱" in o.get("description", "")]
    if not boxes:
        boxes = objs  # 念のため: 箱が見つからなければ全物体から選ぶ
    if not boxes:
        print("物体が見つかりませんでした")
        stop(0.5)
        return

    target = min(boxes, key=lambda o: distance_to(o["x"], o["y"]))
    tx, ty = target["x"], target["y"]
    hx, hy = target["size_x"] / 2.0, target["size_y"] / 2.0
    print("目標:", target["name"], "距離:", round(distance_to(tx, ty), 2))

    def stop_distance():
        # 近づく方向に沿った箱の半幅 + ロボットの前方半長 0.35 m + 余裕 0.1 m
        x, y = get_position()
        a = math.atan2(ty - y, tx - x)
        half_extent = hx * abs(math.cos(a)) + hy * abs(math.sin(a))
        return half_extent + 0.35 + 0.1

    # --- 2. 向きを合わせながら前進する（閉ループ制御） ---
    for _ in range(600):  # 最大 60 秒
        x, y = get_position()
        d = distance_to(tx, ty)
        d_stop = stop_distance()
        if d <= d_stop:
            break

        desired = math.degrees(math.atan2(ty - y, tx - x))
        err = (desired - get_yaw() + 180.0) % 360.0 - 180.0
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))

        if abs(err) > 20.0:
            # 向きが大きくずれている間はその場で旋回
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=0.1)
        else:
            # 向きを微修正しながら前進。目標に近づくほど減速
            vx = max(0.15, min(0.6, 0.8 * (d - d_stop)))
            walk(vx, 0.0, rate, duration=0.1)

    stop(1.0)
    x, y = get_position()
    print("到着:", target["name"], "位置:", (round(x, 2), round(y, 2)),
          "箱の中心までの距離:", round(distance_to(tx, ty), 2))

go_to_nearest_box()
