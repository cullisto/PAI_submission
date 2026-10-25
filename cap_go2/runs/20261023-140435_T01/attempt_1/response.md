# 開始時の位置と向きを記録し、向いている方向への移動距離が 2 m になるまで前進する
# （前方 3.0 m に赤い箱があるが、2 m 地点 (2.0, 0.0) は箱の手前 0.85 m なのでぶつからない）
x0, y0 = get_position()
yaw0 = math.radians(get_yaw())
target_dist = 2.0

for _ in range(400):  # 最大 40 秒
    x, y = get_position()
    # 開始時の向き方向への進んだ距離
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    remaining = target_dist - progress
    if remaining <= 0.02:
        break
    # 目標に近づいたら減速して行き過ぎを防ぐ
    vx = max(0.15, min(0.6, 1.0 * remaining))
    # 向きのずれを小さく補正してまっすぐ進む
    yaw_err = (math.degrees(yaw0) - get_yaw() + 180.0) % 360.0 - 180.0
    yaw_rate = max(-0.3, min(0.3, 1.5 * math.radians(yaw_err)))
    walk(vx, 0.0, yaw_rate, duration=0.1)

stop(1.0)
x, y = get_position()
print("最終位置: ({:.2f}, {:.2f}), 進んだ距離: {:.2f} m".format(
    x, y, (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)))
