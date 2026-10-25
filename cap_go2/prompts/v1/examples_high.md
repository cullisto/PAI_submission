指示: 黄色い箱の方を向いてから、その手前まで歩いて。
```python
# 黄色い箱の位置を取得
bx, by = get_object_position("yellow_box")
# まず箱の方を向く
face(bx, by)
# 箱の中心から 0.5 m 手前（ロボット側）を目標にする
x, y = get_position()
d = math.hypot(bx - x, by - y)
gx = bx - (bx - x) / d * 0.5
gy = by - (by - y) / d * 0.5
reached = move_to(gx, gy, tolerance=0.15)
print("到着:", reached)
stop(0.5)
```

指示: 右に1メートル横歩きしてから、左に45度向きを変えて。
```python
move_sideways(-1.0)  # 右は負
turn(45)  # 左回りは正
stop(0.5)
```
