# 方針:
#  向きは 0 deg(+x 方向)に保ったまま、全方向歩行(vx, vy)で経由点を順にたどる。
#  向きを固定すると胴体の幅 0.3 m(y 方向)で隙間を通れる。旋回中に壁へぶつかる心配もない。
#
# 幾何(get_objects() から計算):
#  wall_upper: y = 1.45 ~ 4.0、wall_lower: y = -3.5 ~ 0.55、x = 1.85 ~ 2.15
#  隙間は y = 0.55 ~ 1.45(中心 y = 1.0、幅 0.9 m)
#  胴体の半幅は 0.15 m なので、中心は y = 0.70 ~ 1.30 の範囲にあれば通れる。
#  胴体の半長は 0.35 m。手前の経由点は壁から x 方向に余裕を取って x = 1.2 とする(前端 1.55 < 1.85)。
#  奥の経由点は x = 2.7 とする(後端 2.35 > 2.15)。ここまで行けば胴体は壁を完全に抜けている。
#  赤い箱(0.3 × 0.3, 中心 (4.0, -1.0))には -x 側から正面で近づく。
#  胴体が当たるのは中心 x = 3.85 - 0.35 = 3.5 なので、少し手前の x = 3.45 を最終目標にする。

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0

# ---- 物体情報から隙間と箱の位置を求める ----
objs = {o["name"]: o for o in get_objects()}
wu = objs["wall_upper"]
wl = objs["wall_lower"]
box = objs["red_box"]

wall_x_min = min(wu["x"] - wu["size_x"] / 2, wl["x"] - wl["size_x"] / 2)
wall_x_max = max(wu["x"] + wu["size_x"] / 2, wl["x"] + wl["size_x"] / 2)
gap_low = wl["y"] + wl["size_y"] / 2      # 0.55
gap_high = wu["y"] - wu["size_y"] / 2     # 1.45
gap_y = (gap_low + gap_high) / 2.0        # 1.0

HALF_LEN = 0.35
MARGIN = 0.3
wp_before = (wall_x_min - HALF_LEN - MARGIN, gap_y)   # (1.2, 1.0)
wp_after = (wall_x_max + HALF_LEN + 0.2, gap_y)       # (2.7, 1.0)
goal = (box["x"] - box["size_x"] / 2 - HALF_LEN - 0.05, box["y"])  # (3.45, -1.0)

print("gap y:", gap_low, "~", gap_high, " waypoints:", wp_before, wp_after, goal)

TARGET_YAW = 0.0   # 常に +x 方向を向いたまま移動する

def go_to(tx, ty, tol=0.08, max_speed=0.5, max_steps=400):
    """向きを TARGET_YAW に保ちながら点 (tx, ty) へ全方向歩行で移動する。"""
    for i in range(max_steps):  # 最大 max_steps * 0.1 秒
        x, y = get_position()
        ex, ey = tx - x, ty - y
        dist = math.hypot(ex, ey)
        if dist < tol:
            print("reached", (round(x, 2), round(y, 2)))
            return True
        # 速度の大きさは近づくほど小さくする(最低速度も設けて停滞を防ぐ)
        speed = clamp(1.0 * dist, 0.15, max_speed)
        vwx, vwy = ex / dist * speed, ey / dist * speed
        # ワールド座標の速度をロボット座標系へ変換する
        yaw = math.radians(get_yaw())
        vx = math.cos(yaw) * vwx + math.sin(yaw) * vwy
        vy = -math.sin(yaw) * vwx + math.cos(yaw) * vwy
        # 向きを保つための旋回指令
        yaw_err = wrap_deg(TARGET_YAW - get_yaw())
        yaw_rate = clamp(2.0 * math.radians(yaw_err), -1.0, 1.0)
        walk(clamp(vx, -0.5, 1.0), clamp(vy, -0.5, 0.5), yaw_rate, duration=0.1)
        if i % 20 == 0:
            print("pos", (round(x, 2), round(y, 2)), "dist", round(dist, 2))
    print("timeout going to", (tx, ty))
    return False

# 1) 隙間の正面(手前)へ移動する。y をしっかり合わせるため許容誤差は小さめにする
go_to(*wp_before, tol=0.06)
stop(0.3)

# 2) 隙間を真っ直ぐ通り抜ける。y は制御で gap_y に保たれる
go_to(*wp_after, tol=0.08, max_speed=0.4)

# 3) 赤い箱の正面まで移動する。箱に当たらない位置で止まる
go_to(*goal, tol=0.05, max_speed=0.4)
stop(1.0)

x, y = get_position()
print("final pos:", (round(x, 2), round(y, 2)),
      "distance to red_box:", round(distance_to(box["x"], box["y"]), 2))
