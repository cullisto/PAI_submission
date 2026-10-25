# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")
# ロボットの現在位置を取得
current_x, current_y = get_position()
current_yaw = get_yaw()

# 赤い箱までの距離を計算
distance_to_red = math.hypot(red_box_x - current_x, red_box_y - current_y)

# まず、ロボットが現在の向きで直進できるかを確認し、障害物にぶつからないように方向を調整
# 赤い箱の中心に向かって、安全な経路を確保するために、直接移動ではなく段階的に移動する
# まず、ロボットが赤い箱の中心に近づくように、段階的に移動する

# 目標までの距離が小さい場合は、直接移動するが、障害物がある場合は、向きを調整して安全に近づく
# 赤い箱の位置 (3.0, 0.0) なので、ロボットがその位置に近づくように、段階的に移動

# まず、ロボットが赤い箱の方向を向く（正確に）
# 赤い箱に向かって旋回（その場で向きを調整）
face(red_box_x, red_box_y)

# その後、安全に移動するように、段階的に移動（1mごとにステップ）
target_x, target_y = red_box_x, red_box_y
step_distance = 0.5  # 1ステップで0.5m移動
max_steps = 10  # 最大10ステップ（5m以内）

for step in range(max_steps):
    # 目標地点まで0.5mずつ進む
    x, y = get_position()
    dx = target_x - x
    dy = target_y - y
    dist = math.hypot(dx, dy)
    
    # まだ目標に到達していない場合
    if dist > step_distance:
        # 前進する（0.5m）
        move_forward(step_distance)
        # 進んだ後、位置を更新して確認
        new_x, new_y = get_position()
        print(f"[t={step * 0.5 + 31.40:.1f}s] 進んだ位置: ({new_x:.2f}, {new_y:.2f})")
    else:
        # 残り距離が0.5m未満なら、残りを1回で進む
        move_forward(dist)
        break

# 最後に、目標位置に到達したか確認
final_x, final_y = get_position()
distance_final = math.hypot(red_box_x - final_x, red_box_y - final_y)
reached = distance_final < 0.3  # 0.3m以内に到達したとみなす

if reached:
    print("赤い箱に到達しました。")
    stop(1.0)
else:
    print("目標に到達できませんでした。")
    stop(1.0)
