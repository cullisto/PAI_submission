```python
# 開始時の位置と向きを記録し、向いている方向への移動距離が 2 m になるまで前進する
x0, y0 = get_position()
yaw0 = math.radians(get_yaw())
for _ in range(300):  # 最大 30 秒
    x, y = get_position()
    progress = (x - x0) * math.cos(yaw0) + (y - y0) * math.sin(yaw0)
    if progress >= 2.0:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(0.5)
```