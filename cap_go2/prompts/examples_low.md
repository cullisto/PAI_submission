指示: 前に1メートル進んで止まって。
```python
# 開始時の位置と向きを記録し、向いている方向への移動距離が 1 m になるまで前進する
x0, y0 = get_position()
yaw0 = math.radians(get_yaw())
for _ in range(300):  # 最大 30 秒
    x, y = get_position()
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    if progress >= 1.0:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(0.5)
```

指示: その場で右に45度回って。
```python
# 目標の向きとの差が小さくなるまで、右回り（負の角速度）で旋回する
target = get_yaw() - 45.0
for _ in range(200):  # 最大 20 秒
    err = (target - get_yaw() + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)
stop(0.5)
```
