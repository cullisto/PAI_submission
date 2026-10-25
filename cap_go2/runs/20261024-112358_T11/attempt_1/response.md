# 方針:
#   赤い箱 (4.0, 0.0) の手前 x=2.0 に横長の壁 (y: -0.8〜0.8) があるため直進できない。
#   壁の左側 (+y 側) を迂回する経由点を物体情報から計算し、順にたどってから箱の正面へ向かう。
#   ロボットの幅 0.3 m (左右 0.15 m)・長さ 0.7 m (前後 0.35 m) に余裕を持たせて経路を決める。

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def angle_diff(target_rad, current_rad):
    # -pi〜pi に正規化した角度差
    return (target_rad - current_rad + math.pi) % (2.0 * math.pi) - math.pi

# --- 物体情報の取得 ---
objs = {o["name"]: o for o in get_objects()}
goal = objs["red_box"]
wall = objs["wall"]

gx, gy = goal["x"], goal["y"]
wall_xmin = wall["x"] - wall["size_x"] / 2.0
wall_xmax = wall["x"] + wall["size_x"] / 2.0
wall_ymax = wall["y"] + wall["size_y"] / 2.0

# --- 経由点の計算 ---
# 壁の側面を通るときの y: 壁の端 + 半幅 0.15 + 余裕 0.35
side_y = wall_ymax + 0.15 + 0.35          # = 1.3
# 壁の手前・奥の x: 前後方向の半長 0.35 + 余裕 0.3
before_x = wall_xmin - 0.65                # = 1.2
after_x = wall_xmax + 0.65                 # = 2.8
# 箱の正面に回り込む点 (箱の手前 x 方向に十分離れた位置)
pre_goal_x = gx - goal["size_x"] / 2.0 - 0.35 - 0.4   # = 3.1

waypoints = [
    (before_x, side_y),
    (after_x, side_y),
    (pre_goal_x, gy),
]
print("waypoints:", waypoints)

def go_to(tx, ty, tol=0.15, max_steps=300):
    # 目標点の方向へ向きを合わせながら前進する (0.1 秒刻み)
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            return True
        err = angle_diff(math.atan2(dy, dx), math.radians(get_yaw()))
        yaw_rate = clamp(2.0 * err, -1.0, 1.0)
        if abs(err) > 0.8:
            vx = 0.0                      # 大きくずれていればその場で旋回
        elif abs(err) > 0.3:
            vx = 0.2
        else:
            vx = clamp(0.8 * dist + 0.2, 0.2, 0.6)
        walk(vx, 0.0, yaw_rate, duration=0.1)
    return False

# --- 経由点を順にたどる ---
for (wx, wy) in waypoints:
    ok = go_to(wx, wy)
    print("reached" if ok else "timeout", (wx, wy), "pos:", get_position())

# --- 箱の方向を向く ---
for _ in range(150):
    x, y = get_position()
    err = angle_diff(math.atan2(gy - y, gx - x), math.radians(get_yaw()))
    if abs(err) < math.radians(3.0):
        break
    rate = clamp(2.0 * err, -1.0, 1.0)
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# --- 箱に正面から近づき、ぶつかる手前で止まる ---
# 箱の中心から (箱の半幅 0.15 + ロボット前方 0.35 + 余裕 0.05) = 0.55 m で停止
stop_dist = goal["size_x"] / 2.0 + 0.35 + 0.05
for _ in range(200):
    d = distance_to(gx, gy)
    if d <= stop_dist:
        break
    x, y = get_position()
    err = angle_diff(math.atan2(gy - y, gx - x), math.radians(get_yaw()))
    vx = clamp(0.8 * (d - stop_dist) + 0.1, 0.1, 0.4)
    walk(vx, 0.0, clamp(2.0 * err, -1.0, 1.0), duration=0.1)

stop(1.0)
print("final pos:", get_position(), "yaw:", get_yaw(), "dist to box:", distance_to(gx, gy))
