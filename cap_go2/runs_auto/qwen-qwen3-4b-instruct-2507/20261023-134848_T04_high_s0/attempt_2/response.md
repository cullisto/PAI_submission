```python
# 青い箱に到達できなかったため、直接その位置へ移動し、障害物を避けずに正確に到達するように修正
# 青い箱の位置を取得
bx, by = get_object_position("blue_box")
# 現在の位置を取得
x, y = get_position()
# 青い箱までの距離を計算
dist_to_blue = math.hypot(bx - x, by - y)

# 青い箱に近づくために、直接移動（安全な距離を確保しながら）
# まず、ロボットが現在の向きを確認し、青い箱に向かって移動
# 青い箱の方向を向く（その場で旋回）
turn_to(bx - x, by - y)  # 向きを調整（atan2で方向を計算）

# 0.5m ずつ進むように段階的に移動（1秒ごとに0.5m進む）
step_distance = 0.5
max_steps = 100  # 最大100ステップ（約50mの移動を想定）
for step in range(max_steps):
    # 現在の位置を取得
    x, y = get_position()
    # 青い箱までの距離を再計算
    dist = math.hypot(bx - x, by - y)
    if dist < 0.3:  # 0.3m以内なら到達
        break
    # 0.5m進む（最大1.0m/sまで）
    move_forward(step_distance)
    # 1秒待つ（安全に移動）
    time.sleep(1.0)
    # タイムアウト防止：120秒以内に終了
    if step > 50:  # 50ステップ以上でタイムアウト
        break

# 到達確認
reached_blue = dist < 0.3
print("青い箱に到達:", reached_blue)

# 青い箱に到達したら、緑の箱へ移動
if reached_blue:
    gx, gy = get_object_position("green_box")
    # 緑の箱へ移動（同じように段階的で安全に）
    turn_to(gx - x, gy - y)
    step_distance = 0.5
    for step in range(max_steps):
        x, y = get_position()
        dist_to_green = math.hypot(gx - x, gy - y)
        if dist_to_green < 0.3:
            break
        move_forward(step_distance)
        time.sleep(1.0)
        if step > 50:
            break
    reached_green = dist_to_green < 0.3
    print("緑の箱に到達:", reached_green)
    if reached_green:
        stop(1.0)
else:
    # 到達できなかった場合、10秒停止
    stop(10.0)
```