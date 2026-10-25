```python
# 開始時の位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 1メートル後ろに下がる（後ろが負方向なので vx は負）
# 向いている方向への移動距離が 1 m になるまで後進する
for _ in range(300):  # 最大 30 秒
    x, y = get_position()
    # ロボットの向きに沿って進んだ距離を計算（向きを考慮）
    progress = (x - x0) * math.cos(math.radians(yaw0)) + (y - y0) * math.sin(math.radians(yaw0))
    if progress <= -1.0:
        break
    walk(-0.5, 0.0, 0.0, duration=0.1)

# 次に右に45度回る（右回りなので yaw_rate は負）
target_yaw = yaw0 + 45.0
for _ in range(200):  # 最大 20 秒
    current_yaw = get_yaw()
    err = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, -rate, duration=0.1)

stop(0.5)
```