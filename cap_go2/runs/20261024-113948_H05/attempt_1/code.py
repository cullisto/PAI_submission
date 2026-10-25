# 方針:
#  - 紫の箱(2.0, 0.3)は直線経路(y=0)の左側にあり、直進すると中心から約0.3 mまで近づいてしまう。
#  - そこで紫の箱の「右側(-y側)」を、中心から約1.7〜1.9 m離れた円弧状の経由点で迂回する。
#    (各区間で紫の箱中心との最短距離を計算済み: 最小でも約1.70 m > 1.5 m)
#  - 最終目標は赤い箱の手前(中心から0.55 m、-x側)。正面から近づくと約0.5 mで胴体が当たるため少し余裕を取る。
#  - 走行中は常に紫の箱との距離を監視し、1.7 mを切りそうなら箱から離れる向きの速度を加える(安全装置)。

px, py = get_object_position("purple_box")
rx, ry = get_object_position("red_box")

SAFE_R = 1.5        # 侵入禁止半径
GUARD_R = 1.7       # この距離を切ったら押し戻しを開始

# 紫の箱の右側(-y側)を回る経由点 + 赤い箱の手前の最終目標
waypoints = [
    (px - 1.2, py - 1.3),   # (0.8, -1.0)
    (px + 0.0, py - 1.9),   # (2.0, -1.6)
    (px + 1.2, py - 1.3),   # (3.2, -1.0)
    (rx - 0.55, ry),        # (3.95, 0.0) 赤い箱の手前
]

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0

min_dist_seen = [1e9]

def purple_dist():
    x, y = get_position()
    return math.hypot(x - px, y - py)

def go_to(tx, ty, tol, final=False, max_steps=400):
    for _ in range(max_steps):  # 最大 max_steps * 0.1 秒
        x, y = get_position()
        yaw = get_yaw()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            return True

        # 目標方向への向き誤差
        heading = math.degrees(math.atan2(dy, dx))
        err = wrap_deg(heading - yaw)
        yaw_rate = clamp(2.0 * math.radians(err), -1.0, 1.0)

        # 向きが合っているほど前進。目標が近いと減速
        speed = 0.6 if not final else clamp(0.8 * dist, 0.15, 0.5)
        vx = speed * max(0.0, math.cos(math.radians(err)))
        if abs(err) > 60.0:
            vx = 0.0  # 大きくずれている間はその場で旋回
        vy = 0.0

        # 安全装置: 紫の箱に近づきすぎたら離れる方向の速度を加える(ボディ座標に変換)
        d = math.hypot(x - px, y - py)
        min_dist_seen[0] = min(min_dist_seen[0], d)
        if d < GUARD_R:
            ax, ay = (x - px) / d, (y - py) / d   # 箱から離れる単位ベクトル(ワールド)
            gain = 0.5 + 2.0 * (GUARD_R - d)
            r = math.radians(yaw)
            vx += gain * (math.cos(r) * ax + math.sin(r) * ay)
            vy += gain * (-math.sin(r) * ax + math.cos(r) * ay)
            print("警告: 紫の箱まで %.2f m のため押し戻し" % d)

        walk(clamp(vx, -0.5, 1.0), clamp(vy, -0.5, 0.5), yaw_rate, duration=0.1)
    return False

# 経由点を順にたどる
for i, (wx, wy) in enumerate(waypoints):
    is_final = (i == len(waypoints) - 1)
    ok = go_to(wx, wy, tol=(0.05 if is_final else 0.2), final=is_final)
    x, y = get_position()
    print("経由点%d (%.2f, %.2f) %s: 現在位置 (%.2f, %.2f), 紫の箱まで %.2f m"
          % (i, wx, wy, "到達" if ok else "タイムアウト", x, y, purple_dist()))

# 最後に赤い箱の方を向く
for _ in range(100):  # 最大 10 秒
    x, y = get_position()
    target = math.degrees(math.atan2(ry - y, rx - x))
    err = wrap_deg(target - get_yaw())
    if abs(err) < 3.0:
        break
    rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)

x, y = get_position()
print("完了: 位置 (%.2f, %.2f), 赤い箱まで %.2f m, 走行中の紫の箱との最小距離 %.2f m (制限 %.1f m)"
      % (x, y, distance_to(rx, ry), min_dist_seen[0], SAFE_R))
