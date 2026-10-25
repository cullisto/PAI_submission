# 目標の向き（左に90度）との差が小さくなるまで、左回り（正の角速度）で旋回する
target = get_yaw() + 90.0
for _ in range(200):  # 最大 20 秒
    err = (target - get_yaw() + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)
