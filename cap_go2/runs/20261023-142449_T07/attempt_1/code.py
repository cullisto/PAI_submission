# 1. 開始時の位置と向きを記録し、後方（向きと逆方向）への移動距離が 1 m になるまで後退する
x0, y0 = get_position()
yaw0 = math.radians(get_yaw())
for _ in range(400):  # 最大 40 秒
    x, y = get_position()
    # 向いている方向への進み量（後退なので負になる）
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    if -progress >= 1.0:
        break
    remaining = 1.0 + progress
    # 残りが少なくなったら減速して行き過ぎを防ぐ
    vx = -0.4 if remaining > 0.2 else -0.2
    walk(vx, 0.0, 0.0, duration=0.1)
stop(0.5)
x, y = get_position()
print("後退後の位置:", (round(x, 2), round(y, 2)))

# 2. 右を向く（現在の向きから右回りに 90 度旋回する）
target = get_yaw() - 90.0
for _ in range(200):  # 最大 20 秒
    err = (target - get_yaw() + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)
print("最終の向き [deg]:", round(get_yaw(), 1))
