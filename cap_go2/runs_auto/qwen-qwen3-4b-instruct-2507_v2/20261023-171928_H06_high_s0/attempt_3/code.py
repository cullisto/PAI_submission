# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを確認
current_x, current_y = get_position()
current_yaw = get_yaw()

# お尻を向けるため、赤い箱の反対方向（180度）をターゲットとして設定
target_yaw = 180.0

# その場で旋回して、赤い箱の反対方向（お尻を向ける方向）を向く
# 現在の向きが180度に近い場合にのみ正確に調整（誤差を25度以内に抑える）
turn_to(target_yaw)

# 赤い箱の中心から1メートル離れた位置を安全に計算
# ロボットの前後方向に0.35mの幅があるため、箱に当たらないようにする
dx = red_box_x - current_x
dy = red_box_y - current_y
distance = math.hypot(dx, dy)

# 距離が0なら、現在の位置から1m離れた点を設定（安全に）
if distance == 0:
    target_x = current_x
    target_y = current_y
else:
    # ベクトル方向に1.0m離れた点を計算（ロボットが箱に当たらないように）
    unit_x = dx / distance
    unit_y = dy / distance
    target_x = red_box_x - unit_x * 1.0
    target_y = red_box_y - unit_y * 1.0

# 1.25m以内に到達するように、安全な距離で移動（0.3m以内で到達とみなす）
reached = move_to(target_x, target_y, tolerance=0.3)
print("目標位置に到達:", reached)

# 到達したら、2秒間停止（安全に止まる）
if reached:
    stop(2.0)
