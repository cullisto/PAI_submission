```python
# 赤い箱と青い箱の中心座標を取得
red_box_pos = get_object_position("red_box")  # (3.0, 0.0)
blue_box_pos = get_object_position("blue_box")  # (2.0, 2.0)

# 両方の箱の中心のちょうど中間の座標を計算
mid_x = (red_box_pos[0] + blue_box_pos[0]) / 2.0
mid_y = (red_box_pos[1] + blue_box_pos[1]) / 2.0

# 中間地点に移動する（障害物を避けないが、到達するまで歩く）
reached = move_to(mid_x, mid_y, tolerance=0.3)
print("中間地点に到着:", reached)

# 到達したら停止
if reached:
    stop(1.0)
```