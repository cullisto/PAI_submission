# 方針:
#  1. 開始位置・向きを記録し、ロボットの左側 R [m] の点を円の中心にする
#     （開始時 (0,0)・0 deg なら中心は (0, 1.0)。円は x∈[-1,1], y∈[0,2] の範囲で、
#      どの箱からも 1 m 以上離れているのでぶつからない）
#  2. 前進しながら左旋回し、半径のずれと進行方向のずれをフィードバックで補正して円を描く
#  3. 中心から見た角度が 1 周(360 deg)分進んだら円走行を終了
#  4. 開始位置とのずれを前後・左右の速度で補正して元の場所に戻り、最初の向きに合わせる

def wrap_rad(a):
    # 角度を -pi〜pi に正規化
    return (a + math.pi) % (2.0 * math.pi) - math.pi

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def circle_and_return():
    R = 1.0          # 円の半径 [m]
    V = 0.5          # 前進速度 [m/s]
    DT = 0.1         # 制御周期 [s]

    x0, y0 = get_position()
    yaw0_deg = get_yaw()
    th0 = math.radians(yaw0_deg)

    # 左回りの円なので、中心はロボットの左側 R [m]
    cx = x0 - R * math.sin(th0)
    cy = y0 + R * math.cos(th0)
    print("start=(%.2f, %.2f) yaw=%.1f, circle center=(%.2f, %.2f)" % (x0, y0, yaw0_deg, cx, cy))

    # ---- 円を描いて一周 ----
    base_rate = V / R                    # 理想的な旋回角速度 [rad/s]
    phi_prev = math.atan2(y0 - cy, x0 - cx)
    phi_total = 0.0                      # 中心から見て進んだ角度の累計 [rad]

    for i in range(450):  # 最大 45 秒（一周の目安は約 12.6 秒）
        x, y = get_position()
        yaw = math.radians(get_yaw())

        phi = math.atan2(y - cy, x - cx)
        phi_total += wrap_rad(phi - phi_prev)
        phi_prev = phi

        # 一周したら終了（最後の少しは戻り動作で補正する）
        if phi_total >= 2.0 * math.pi - math.radians(10.0):
            break

        r = math.hypot(x - cx, y - cy)
        radial_err = r - R                       # 正なら外側にずれている → もっと左に曲がる
        tangent = phi + math.pi / 2.0            # 左回りの円の接線方向
        heading_err = wrap_rad(tangent - yaw)    # 正なら左に向きを直す

        rate = base_rate + 1.0 * radial_err + 1.5 * heading_err
        rate = clamp(rate, -1.0, 1.0)
        walk(V, 0.0, rate, duration=DT)

        if i % 10 == 0:
            print("t=%.1fs pos=(%.2f, %.2f) r=%.2f progress=%.0f deg"
                  % (i * DT, x, y, r, math.degrees(phi_total)))

    print("circle done: progress=%.0f deg" % math.degrees(phi_total))

    # ---- 開始位置へ戻る（向きは変えずに前後・左右移動で補正）----
    for _ in range(200):  # 最大 20 秒
        x, y = get_position()
        d = distance_to(x0, y0)
        if d < 0.1:
            break
        yaw = math.radians(get_yaw())
        dx, dy = x0 - x, y0 - y
        # ワールド座標のずれをロボット座標に変換
        bx = math.cos(yaw) * dx + math.sin(yaw) * dy
        by = -math.sin(yaw) * dx + math.cos(yaw) * dy
        speed = clamp(0.8 * d, 0.15, 0.4)
        n = math.hypot(bx, by)
        walk(clamp(speed * bx / n, -0.5, 1.0), clamp(speed * by / n, -0.5, 0.5), 0.0, duration=DT)

    # ---- 最初の向きに合わせる ----
    for _ in range(150):  # 最大 15 秒
        err = (yaw0_deg - get_yaw() + 180.0) % 360.0 - 180.0
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=DT)

    stop(0.5)
    xf, yf = get_position()
    print("final pos=(%.2f, %.2f) yaw=%.1f, distance from start=%.2f m"
          % (xf, yf, get_yaw(), distance_to(x0, y0)))

circle_and_return()
