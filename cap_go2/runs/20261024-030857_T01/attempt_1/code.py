# 開始時の位置と向きを記録し、その向きへの移動距離が 2 m になるまで前進する。
# 前方の red_box（中心 (3.0, 0.0)、表面 x=2.85）までは、2 m 進んでもロボット前端は x≈2.35 なので衝突しない。
x0, y0 = get_position()
yaw0_deg = get_yaw()
yaw0 = math.radians(yaw0_deg)
target_dist = 2.0

for _ in range(600):  # 最大 60 秒
    x, y = get_position()
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    remaining = target_dist - progress
    if remaining <= 0.02:
        break
    # 目標に近づいたら減速してオーバーシュートを防ぐ
    vx = max(0.15, min(0.6, 1.0 * remaining))
    # 開始時の向きを保つよう、向きのずれを小さく補正する
    yaw_err = (yaw0_deg - get_yaw() + 180.0) % 360.0 - 180.0
    yaw_rate = max(-0.3, min(0.3, 1.5 * math.radians(yaw_err)))
    walk(vx, 0.0, yaw_rate, duration=0.1)

stop(1.0)
x, y = get_position()
print("final position:", (round(x, 3), round(y, 3)), "yaw:", round(get_yaw(), 1))
