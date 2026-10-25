```python
# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")
# ロボットの現在位置と向きを確認
current_x, current_y = get_position()
current_yaw = get_yaw()

# 赤い箱に向かって移動（障害物を避けないが、直接到達を目指す）
# 到達までの距離を計算
distance_to_red = math.hypot(red_box_x - current_x, red_box_y - current_y)
# 目標位置を設定（赤い箱の中心に到達）
reached = move_to(red_box_x, red_box_y, tolerance=0.3)
print("赤い箱への移動結果:", reached)

# 到達した場合、少し止める
if reached:
    stop(1.0)
```