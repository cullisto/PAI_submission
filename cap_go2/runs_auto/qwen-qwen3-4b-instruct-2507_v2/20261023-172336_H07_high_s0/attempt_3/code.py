# 青い箱の位置を取得
bx, by = get_object_position("blue_box")

# 現在の位置を取得
x, y = get_position()

# 箱の中心からロボットの中心までの距離を計算
d = math.hypot(bx - x, by - y)

# ロボットの前後方向に0.35mの余裕をもつように、手前まで移動する
# ただし、安全距離（0.35m）を確保するため、移動距離は d - 0.35 で計算
# d が 0.35m 未満なら、すでに安全距離内にあるため、移動距離は0

# 前後方向に移動する距離（手前へ）
move_distance = max(0, d - 0.35)

# 前後方向に移動（左右の移動はしない）
if move_distance > 0:
    move_forward(move_distance)

# ロボットの向きは変更しない（指示通り、向きを変えずに前後移動）
stop(0.5)
