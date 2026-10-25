```python
# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")
# ロボットの現在位置を取得
current_x, current_y = get_position()
current_yaw = get_yaw()

# 赤い箱までの距離を計算
distance_to_red = math.hypot(red_box_x - current_x, red_box_y - current_y)

# 直接 move_to を使うのではなく、安全に移動するように、まず向きを調整し、段階的に移動
# 1. 赤い箱に向かって旋回（その場で向きを調整）
face(red_box_x, red_box_y)

# 2. 目標までの距離が小さい場合、直接移動するように、移動量を小さくして安全に近づく
# 3. 途中で障害物にぶつからないように、移動を制御（移動量は0.3mまでに抑える）

target_x, target_y = red_box_x, red_box_y
max_steps = 20
step_distance = 0.3  # 1ステップで0.3m移動（安全なステップ）

for step in range(max_steps):
    # 現在の位置を取得
    x, y = get_position()
    dx = target_x - x
    dy = target_y - y
    dist = math.hypot(dx, dy)
    
    # 残り距離が0.3m以下なら、1回で移動
    if dist <= step_distance:
        move_forward(dist)
        break
    else:
        # 0.3mずつ前に進む
        move_forward(step_distance)
        # 進んだ後、位置を確認（ログ出力）
        new_x, new_y = get_position()
        print(f"[t={step * 0.3 + 2.60:.1f}s] 進んだ位置: ({new_x:.2f}, {new_y:.2f})")
else:
    # 最大ステップまで進んでも目標に到達しなかった場合
    print("目標に到達できませんでした。")

# 最終位置を確認
final_x, final_y = get_position()
final_distance = math.hypot(red_box_x - final_x, red_box_y - final_y)
reached = final_distance < 0.3

if reached:
    print("赤い箱に安全に到達しました。")
    stop(1.0)
else:
    print("目標に到達できませんでした。")
    stop(1.0)
```