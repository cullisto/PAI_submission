# 1辺1mの正方形を左回りで歩く: (0,0) → (1,0) → (1,1) → (0,1) → (0,0)
# 各角でその場旋回して次の辺の方向を向き、目標点に向かって前進する。
# 箱はどれもこの正方形から十分離れているので、ぶつかる心配はない。

def angle_diff(target, current):
    # target - current を -180〜180 deg に正規化
    return (target - current + 180.0) % 360.0 - 180.0

def turn_to(target_yaw, tol=2.0):
    # 目標の向きまでその場で旋回する
    for _ in range(200):  # 最大 20 秒
        err = angle_diff(target_yaw, get_yaw())
        if abs(err) < tol:
            break
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)
    stop(0.3)

def walk_to(tx, ty, tol=0.05):
    # 目標点の方向に向きを補正しながら前進する
    for _ in range(300):  # 最大 30 秒
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            break
        bearing = math.degrees(math.atan2(dy, dx))
        err = angle_diff(bearing, get_yaw())
        yaw_rate = max(-1.0, min(1.0, 1.5 * math.radians(err)))
        # 向きが大きくずれている間は前進を抑え、目標に近づいたら減速
        if abs(err) > 30.0:
            vx = 0.0
        else:
            vx = max(0.15, min(0.5, 1.0 * dist))
        walk(vx, 0.0, yaw_rate, duration=0.1)
    stop(0.3)

def draw_square(side=1.0):
    x0, y0 = get_position()
    yaw0 = get_yaw()
    th = math.radians(yaw0)
    # ロボット自身から見て「前 → 左 → 後ろ → 右」の順に角を回る（左回りの正方形）
    local_corners = [(side, 0.0), (side, side), (0.0, side), (0.0, 0.0)]
    for i, (lx, ly) in enumerate(local_corners):
        # ロボット座標の角をワールド座標に変換
        cx = x0 + lx * math.cos(th) - ly * math.sin(th)
        cy = y0 + lx * math.sin(th) + ly * math.cos(th)
        # この辺の進行方向を向いてから歩く（i 番目の辺は yaw0 + 90*i 度）
        turn_to(yaw0 + 90.0 * i)
        print("corner", i + 1, "target:", round(cx, 2), round(cy, 2))
        walk_to(cx, cy)
        print("reached:", get_position(), "yaw:", round(get_yaw(), 1))
    # 最後に元の向きに戻す
    turn_to(yaw0)
    stop(0.5)
    print("done. final position:", get_position(), "yaw:", round(get_yaw(), 1))

draw_square(1.0)
