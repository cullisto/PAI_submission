# 赤い箱の中心から 1.0 m 離れた点に移動し、お尻（後ろ）を箱へ向けて止まる。
# 目標の向き = 箱からロボットへ向かう方向（箱に背を向ける向き）。
# 箱は 0.3 m 四方なので、箱の表面からロボット中心までの最低距離は 0.15 + 0.35 = 0.5 m。
# 1.0 m なら後ろの脚が箱に当たらない。

def wrap_deg(a):
    # 角度を -180〜180 deg に正規化する
    return (a + 180.0) % 360.0 - 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ---- 目標位置と目標の向きを決める ----
bx, by = get_object_position("red_box")
x0, y0 = get_position()
dx, dy = x0 - bx, y0 - by
d0 = math.hypot(dx, dy)
if d0 < 1e-3:
    ux, uy = -1.0, 0.0   # 念のため（通常は起こらない）
else:
    ux, uy = dx / d0, dy / d0   # 箱からロボットへ向かう単位ベクトル

tx = bx + 1.0 * ux   # 箱から 1 m 離れた、現在位置側の点
ty = by + 1.0 * uy
final_yaw = math.degrees(math.atan2(uy, ux))   # 箱と反対を向く = お尻が箱を向く
print("target:", round(tx, 3), round(ty, 3), "final yaw:", round(final_yaw, 1))


def turn_to(target_yaw, tol=2.0, max_steps=200):
    # 目標の向きとの差が tol 以下になるまでその場で旋回する
    for _ in range(max_steps):
        err = wrap_deg(target_yaw - get_yaw())
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)


# ---- フェーズ1: 目標点の方を向いて前進（大まかに近づく）----
for _ in range(400):  # 最大 40 秒
    x, y = get_position()
    ex, ey = tx - x, ty - y
    dist = math.hypot(ex, ey)
    if dist < 0.15:
        break
    heading = math.degrees(math.atan2(ey, ex))
    err = wrap_deg(heading - get_yaw())
    if abs(err) > 30.0:
        # 大きくずれていたらその場で向きを合わせる
        turn_to(heading, tol=5.0, max_steps=100)
        continue
    vx = clamp(0.8 * dist, 0.2, 0.8)
    yaw_rate = clamp(1.5 * math.radians(err), -1.0, 1.0)
    walk(vx, 0.0, yaw_rate, duration=0.1)
stop(0.3)

# ---- フェーズ2: 箱にお尻を向ける向きに旋回 ----
turn_to(final_yaw, tol=2.0)
stop(0.3)

# ---- フェーズ3: 向きを保ったまま前後左右に動いて位置を微調整 ----
for _ in range(200):  # 最大 20 秒
    x, y = get_position()
    ex, ey = tx - x, ty - y
    if math.hypot(ex, ey) < 0.04:
        break
    yaw = get_yaw()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    # ワールド座標の誤差をロボット座標に変換
    e_fwd = c * ex + s * ey
    e_left = -s * ex + c * ey
    vx = clamp(1.2 * e_fwd, -0.3, 0.3)
    vy = clamp(1.2 * e_left, -0.3, 0.3)
    yaw_err = wrap_deg(final_yaw - yaw)
    yaw_rate = clamp(1.5 * math.radians(yaw_err), -0.5, 0.5)
    walk(vx, vy, yaw_rate, duration=0.1)
stop(0.3)

# 最後に向きをもう一度整える
turn_to(final_yaw, tol=2.0, max_steps=50)
stop(1.0)

x, y = get_position()
print("final pos:", round(x, 3), round(y, 3),
      "dist to red_box:", round(distance_to(bx, by), 3),
      "yaw:", round(get_yaw(), 1))
