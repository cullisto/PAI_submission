```python
# すべての箱の位置を取得して、ロボットの現在位置から最も近い箱を選び、その中心に向かって移動する
objects = get_objects()
current_x, current_y = get_position()

# 各箱までの距離を計算し、最も近い箱を決定
min_distance = float('inf')
closest_object = None

for obj in objects:
    obj_x, obj_y = obj['x'], obj['y']
    dist = math.hypot(obj_x - current_x, obj_y - current_y)
    if dist < min_distance:
        min_distance = dist
        closest_object = obj

# 最も近い箱の位置に移動（障害物を避ける必要なし）
if closest_object:
    target_x, target_y = closest_object['x'], closest_object['y']
    reached = move_to(target_x, target_y, tolerance=0.3)
    print("到着:", reached)
else:
    print("物体が見つかりません。")
```