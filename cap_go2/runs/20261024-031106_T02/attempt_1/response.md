# 開始時の向きから左回り（正の角速度）に 90 度回転する
# 目標との角度差が小さくなるまで、差に比例した角速度で旋回する
target = get_yaw() + 90.0
for _ in range(200):  # 最大 20 秒
    # 目標との差を -180〜180 deg に正規化
    err = (target - get_yaw() + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    # 比例制御（範囲 -1.0〜1.0 に制限）、小さすぎると回らないので最低 0.3 rad/s を確保
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)
print("final yaw:", get_yaw())
