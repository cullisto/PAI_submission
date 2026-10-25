# 1) 開始時の位置と向きを記録し、向いている方向と逆向き（後ろ）への移動距離が 1 m になるまで後退する
x0, y0 = get_position()
yaw0 = math.radians(get_yaw())
for _ in range(400):  # 最大 40 秒
    x, y = get_position()
    # 開始時の向きに沿った移動量（前が正）。後退なので -1.0 以下になったら終了
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    if progress <= -1.0:
        break
    remaining = 1.0 + progress  # 残りの後退距離
    # 残りが少なくなったら減速して行き過ぎを防ぐ
    vx = -0.5 if remaining > 0.2 else -0.25
    walk(vx, 0.0, 0.0, duration=0.1)
stop(0.5)
print("後退後の位置:", get_position(), "向き:", get_yaw())

# 2) その場で右（時計回り）に 90 度旋回して右を向く
target = get_yaw() - 90.0
for _ in range(300):  # 最大 30 秒
    err = (target - get_yaw() + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)
print("最終位置:", get_position(), "最終向き:", get_yaw())
