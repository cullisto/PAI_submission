# 方針:
#   開始位置から左回り（反時計回り）に半径 R の円を一周する。
#   円の中心は開始時の向きから見て左側 R [m] の点。
#   R = 0.5 m なら軌道は x: -0.5〜0.5, y: 0〜1.0 の範囲に収まり、どの箱にもぶつからない。
#   一周の判定には、向きの変化量 (yaw の差分) の累積を使う。
#   最後に開始位置との誤差を閉ループで補正し、向きも開始時の向きに戻す。

R = 0.5          # 円の半径 [m]
V = 0.4          # 前進速度 [m/s]
DT = 0.1         # 1 ステップの時間 [s]

def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def draw_circle():
    x0, y0 = get_position()
    yaw0_deg = get_yaw()
    yaw0 = math.radians(yaw0_deg)
    # 円の中心：開始時の向きから見て左側 R [m]
    cx = x0 - R * math.sin(yaw0)
    cy = y0 + R * math.cos(yaw0)
    print("start:", (round(x0, 2), round(y0, 2)), "yaw:", round(yaw0_deg, 1),
          "center:", (round(cx, 2), round(cy, 2)))

    # --- 1. 円周を一周する ---
    base_rate = V / R            # 半径 R の円に必要な角速度 [rad/s]
    turned = 0.0                 # 累積旋回角 [deg]
    prev_yaw = yaw0_deg
    for i in range(400):         # 最大 40 秒
        if turned >= 360.0:
            break
        x, y = get_position()
        d = math.hypot(x - cx, y - cy)
        # 中心から遠すぎれば強く左旋回、近すぎれば緩める（半径の補正）
        rate = clamp(base_rate + 1.0 * (d - R), 0.2, 1.0)
        # 終盤は速度を落として行き過ぎを防ぐ
        remaining = 360.0 - turned
        scale = 1.0 if remaining > 30.0 else max(0.4, remaining / 30.0)
        walk(V * scale, 0.0, rate * scale, duration=DT)
        yaw = get_yaw()
        turned += wrap_deg(yaw - prev_yaw)
        prev_yaw = yaw
        if i % 10 == 0:
            print("turned:", round(turned, 1), "pos:", (round(x, 2), round(y, 2)),
                  "r:", round(d, 2))
    stop(0.5)
    print("circle done. turned:", round(turned, 1), "pos:", get_position(),
          "dist to start:", round(distance_to(x0, y0), 3))

    # --- 2. 開始位置とのずれを補正する（前後・左右の移動で寄せる） ---
    for _ in range(150):         # 最大 15 秒
        x, y = get_position()
        ex, ey = x0 - x, y0 - y
        if math.hypot(ex, ey) < 0.05:
            break
        yaw = math.radians(get_yaw())
        # ワールド座標の誤差をロボット座標系に変換
        fx = ex * math.cos(yaw) + ey * math.sin(yaw)
        fy = -ex * math.sin(yaw) + ey * math.cos(yaw)
        vx = clamp(1.5 * fx, -0.4, 0.4)
        vy = clamp(1.5 * fy, -0.4, 0.4)
        # 小さすぎる指令では動かないことがあるので最低速度を確保
        n = math.hypot(vx, vy)
        if 0.0 < n < 0.15:
            vx, vy = vx * 0.15 / n, vy * 0.15 / n
        walk(vx, vy, 0.0, duration=DT)
    stop(0.3)

    # --- 3. 向きを開始時の向きに戻す ---
    for _ in range(100):         # 最大 10 秒
        err = wrap_deg(yaw0_deg - get_yaw())
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=DT)
    stop(0.5)

    print("final pos:", get_position(), "yaw:", round(get_yaw(), 1),
          "dist to start:", round(distance_to(x0, y0), 3))

draw_circle()
