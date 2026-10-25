# 方針:
#   1. get_objects() から 2 枚の壁の y 範囲を求め、隙間の中心 y と壁の x 範囲を計算する
#   2. 隙間の手前 (壁の手前 0.7 m) の点へ移動し、+x 方向(0 deg)を向く
#   3. 隙間の中心線に沿ってまっすぐ前進し、壁の向こう側 (壁の奥 0.6 m) まで抜ける
#   4. 赤い箱の方を向いて近づき、ぶつからない距離 (中心から約 0.55 m) で止まる

def normalize_deg(a):
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ---- 1. 隙間の位置を計算 ----
walls = [o for o in get_objects() if o["is_obstacle"]]
gap_y = 1.0          # 既定値（環境説明より: 下壁上端 0.55, 上壁下端 1.45）
wall_x_min, wall_x_max = 1.85, 2.15
if len(walls) >= 2:
    walls.sort(key=lambda o: o["y"])
    lower, upper = walls[0], walls[-1]
    lower_top = lower["y"] + lower["size_y"] / 2.0
    upper_bottom = upper["y"] - upper["size_y"] / 2.0
    gap_y = (lower_top + upper_bottom) / 2.0
    wall_x_min = min(w["x"] - w["size_x"] / 2.0 for w in walls)
    wall_x_max = max(w["x"] + w["size_x"] / 2.0 for w in walls)
    print("gap: y=%.3f (%.3f..%.3f), wall x=%.2f..%.2f"
          % (gap_y, lower_top, upper_bottom, wall_x_min, wall_x_max))

box_x, box_y = get_object_position("red_box")

# ---- 汎用関数 ----
def turn_to(target_deg, tol=3.0, max_steps=150):
    # 指定の向きになるまでその場で旋回
    for _ in range(max_steps):
        err = normalize_deg(target_deg - get_yaw())
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

def go_to(tx, ty, reach=0.08, max_speed=0.5, max_steps=400):
    # 目標点の方向を向きながら前進。向きのずれが大きいときはその場で旋回する
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < reach:
            return True
        heading = math.degrees(math.atan2(dy, dx))
        err = normalize_deg(heading - get_yaw())
        if abs(err) > 25.0:
            turn_to(heading, tol=5.0, max_steps=60)
            continue
        vx = clamp(1.2 * dist, 0.15, max_speed)
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        walk(vx, 0.0, rate, duration=0.1)
    return False

def pass_gap(x_end, y_line, max_steps=300):
    # +x 方向を向いたまま、y = y_line の線に沿って x_end まで直進する
    # (横ずれは vy、向きのずれは yaw_rate で補正)
    for _ in range(max_steps):
        x, y = get_position()
        if x >= x_end:
            return True
        yaw = get_yaw()
        yaw_err = math.radians(normalize_deg(0.0 - yaw))
        # 横方向の誤差をロボット座標系の vy に変換（0 deg 付近なのでほぼ ey）
        ey = y_line - y
        vy = clamp(1.5 * ey * math.cos(math.radians(yaw)), -0.3, 0.3)
        walk(0.4, vy, clamp(2.0 * yaw_err, -0.8, 0.8), duration=0.1)
    return False

# ---- 2. 隙間の手前へ ----
approach_x = wall_x_min - 0.7
print("隙間の手前へ移動:", (round(approach_x, 2), round(gap_y, 2)))
go_to(approach_x, gap_y, reach=0.06)
turn_to(0.0)
stop(0.3)

# ---- 3. 隙間を通り抜ける ----
exit_x = wall_x_max + 0.6
print("隙間を通過中...")
pass_gap(exit_x, gap_y)
stop(0.3)
print("通過後の位置:", get_position())

# ---- 4. 赤い箱へ近づいて止まる ----
STOP_DIST = 0.55  # 箱の中心からこの距離で停止（箱の半幅 0.15 + 胴体前半分 + 余裕）
x, y = get_position()
turn_to(math.degrees(math.atan2(box_y - y, box_x - x)), tol=4.0)
for _ in range(300):
    d = distance_to(box_x, box_y)
    if d <= STOP_DIST:
        break
    x, y = get_position()
    heading = math.degrees(math.atan2(box_y - y, box_x - x))
    err = normalize_deg(heading - get_yaw())
    if abs(err) > 25.0:
        turn_to(heading, tol=5.0, max_steps=60)
        continue
    vx = clamp(1.2 * (d - STOP_DIST), 0.15, 0.5)
    walk(vx, 0.0, clamp(2.0 * math.radians(err), -1.0, 1.0), duration=0.1)

stop(1.0)
print("到着: 位置", get_position(), "向き", round(get_yaw(), 1),
      "箱までの距離", round(distance_to(box_x, box_y), 2))
