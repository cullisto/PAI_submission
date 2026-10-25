# 左回り（反時計回り）に半径 r の円を一周し、スタート地点付近に戻る。
# walk() で前進速度と旋回角速度を与えて円弧を描き、位置と向きを見ながら毎ステップ補正する。

start_x, start_y = get_position()
start_yaw = get_yaw()
yaw0 = math.radians(start_yaw)

def wrap_rad(a):
    # 角度を -pi〜pi に正規化
    return math.atan2(math.sin(a), math.cos(a))

# --- 半径の決定: 箱にぶつからない半径を候補から選ぶ ---
# 左回りなので、円の中心はロボットの左側（向きに対して +90 deg 方向）
def circle_center(r):
    return (start_x + r * math.cos(yaw0 + math.pi / 2),
            start_y + r * math.sin(yaw0 + math.pi / 2))

def is_safe(r):
    cx, cy = circle_center(r)
    for obj in get_objects():
        d = math.hypot(obj["x"] - cx, obj["y"] - cy)
        # 箱の半分の大きさ + ロボットの半身長(0.35) + 余裕 0.15
        margin = max(obj["size_x"], obj["size_y"]) / 2 + 0.35 + 0.15
        if abs(d - r) < margin:
            return False
    return True

radius = 0.6
for r in [1.0, 0.9, 0.8, 0.7, 0.6]:
    if is_safe(r):
        radius = r
        break
cx, cy = circle_center(radius)
print("半径:", radius, "円の中心:", (round(cx, 2), round(cy, 2)))

# --- 円周に沿って歩く（フィードバック付き） ---
v = 0.5                 # 前進速度 [m/s]
omega = v / radius      # 円を描くための基本の旋回角速度 [rad/s]
dt = 0.2                # 1 ステップの時間 [s]
k_heading = 1.0         # 向きのずれの補正ゲイン
k_radial = 0.8          # 半径のずれの補正ゲイン

x, y = get_position()
prev_phi = math.atan2(y - cy, x - cx)
progress = 0.0          # 中心まわりに進んだ角度の累計 [rad]
max_steps = 300         # 最大 60 秒

for i in range(max_steps):
    x, y = get_position()
    yaw = math.radians(get_yaw())

    # 中心まわりの角度の進み（左回りで増える）
    phi = math.atan2(y - cy, x - cx)
    progress += wrap_rad(phi - prev_phi)
    prev_phi = phi
    if progress >= 2 * math.pi - 0.08:
        break

    # 円の接線方向（左回り）と現在の向きのずれ
    tangent = phi + math.pi / 2
    heading_err = wrap_rad(tangent - yaw)
    # 半径のずれ（外側にいるときは正 → 左へ多めに曲がる）
    radial_err = math.hypot(x - cx, y - cy) - radius

    yaw_rate = omega + k_heading * heading_err + k_radial * radial_err
    yaw_rate = max(-1.0, min(1.0, yaw_rate))
    walk(v, 0.0, yaw_rate, dt)

    if i % 10 == 0:
        print("step", i, "位置", (round(x, 2), round(y, 2)),
              "進んだ角度", round(math.degrees(progress)), "deg")

print("円周走行終了: 進んだ角度", round(math.degrees(progress)), "deg")

# --- 元の場所へ戻って、最初の向きにそろえる ---
reached = move_to(start_x, start_y, tolerance=0.15, timeout=15.0)
turn_to(start_yaw)
stop(0.5)

fx, fy = get_position()
print("帰着:", reached, "最終位置:", (round(fx, 2), round(fy, 2)),
      "スタートからの距離:", round(distance_to(start_x, start_y), 2), "m")
