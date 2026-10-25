# 方針:
#   赤い箱 (4.0, 0.0) とロボット (0.0, 0.0) の間に壁 (中心 2.0, 0.0 / 0.3 x 1.6) があり、
#   直進すると衝突する。壁の y 範囲は -0.8〜0.8 なので、左側 (+y 側) に余裕を持って回り込む。
#   経由点: 壁の手前左 → 壁の奥左 → 箱の手前 (箱の中心には入れないので 0.55 m 手前で止まる)
#   各経由点へは「目標方向を向きながら、ロボット座標系に変換した速度で歩く」制御で移動する。

def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def go_to(tx, ty, tol=0.15, max_steps=400, max_speed=0.5):
    # 点 (tx, ty) に tol [m] 以内まで近づく（最大 max_steps * 0.1 秒）
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            return True
        yaw = get_yaw()
        desired = math.degrees(math.atan2(dy, dx))
        err = wrap_deg(desired - yaw)
        # 旋回: 目標方向を向くように比例制御
        yaw_rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
        # ワールド座標の誤差をロボット座標系に変換
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        ex = c * dx + s * dy
        ey = -s * dx + c * dy
        if abs(err) > 45.0:
            # 向きが大きくずれているときはその場で旋回を優先
            vx, vy = 0.0, 0.0
            if abs(yaw_rate) < 0.3:
                yaw_rate = math.copysign(0.3, yaw_rate)
        else:
            speed = clamp(0.8 * dist, 0.15, max_speed)
            vx = clamp(ex / dist * speed, -0.3, 1.0)
            vy = clamp(ey / dist * speed, -0.3, 0.3)
        walk(vx, vy, yaw_rate, duration=0.1)
    print("go_to: 回数上限に到達", (tx, ty), get_position())
    return False

def turn_to(target_yaw, max_steps=150):
    # 指定の向き [deg] になるまでその場で旋回
    for _ in range(max_steps):
        err = wrap_deg(target_yaw - get_yaw())
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

def main():
    # ゴールと障害物の情報を取得
    gx, gy = get_object_position("red_box")
    obstacles = [o for o in get_objects() if o["is_obstacle"]]

    rx, ry = get_position()
    approach = 0.55  # 箱の中心からこの距離で止まる
    waypoints = []

    for o in obstacles:
        x_min = o["x"] - o["size_x"] / 2.0
        x_max = o["x"] + o["size_x"] / 2.0
        y_min = o["y"] - o["size_y"] / 2.0
        y_max = o["y"] + o["size_y"] / 2.0
        # ロボットとゴールの間にあり、直線経路 (y≈0付近) を塞いでいるか
        between = min(rx, gx) < x_max and x_min < max(rx, gx)
        path_y = (ry + gy) / 2.0
        blocking = (y_min - 0.4) < path_y < (y_max + 0.4)
        if between and blocking:
            # 左 (+y) と右 (-y) のうち、回り込みが短い側を選ぶ
            margin = 0.55  # ロボットの胴体幅・旋回時のはみ出しを考慮した余裕
            left_y = y_max + margin
            right_y = y_min - margin
            side_y = left_y if abs(left_y - path_y) <= abs(right_y - path_y) else right_y
            waypoints.append((x_min - 0.6, side_y))  # 壁の手前
            waypoints.append((x_max + 0.6, side_y))  # 壁の奥
            print("障害物を回避:", o["name"], "経由 y =", side_y)

    # 最後に箱の手前（最後の経由点側から近づく）
    lx, ly = waypoints[-1] if waypoints else (rx, ry)
    d = math.hypot(gx - lx, gy - ly)
    final = (gx - (gx - lx) / d * approach, gy - (gy - ly) / d * approach)
    waypoints.append(final)

    for i, (wx, wy) in enumerate(waypoints):
        tol = 0.1 if i == len(waypoints) - 1 else 0.2
        go_to(wx, wy, tol=tol)
        print("経由点", i, "到達:", get_position())

    stop(0.3)
    # 箱の方を向いて止まる
    x, y = get_position()
    turn_to(math.degrees(math.atan2(gy - y, gx - x)))
    stop(1.0)
    print("最終位置:", get_position(), "向き:", get_yaw(), "箱までの距離:", distance_to(gx, gy))

main()
