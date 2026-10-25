# 青い箱の位置を取得
bx, by = get_object_position("blue_box")

# 現在の位置を取得
x, y = get_position()

# 箱の中心からロボットの胴体が当たらないように、0.35m（前後）と0.15m（左右）の余裕をもって手前まで移動
# 前後方向の距離を計算（x方向）
dx = bx - x
# 箱の中心からロボットの中心までの距離
d = math.hypot(dx, by - y)

# 前後方向に移動する距離を計算（ロボットの前後幅0.35mを考慮して、箱に近づく）
# 0.35mの余裕をもつように、手前まで0.35m以内に近づく
target_distance = 0.35  # 前後方向の安全距離

# 前後方向に移動する距離（手前へ）
move_distance = d - target_distance

# 前後方向に移動（左右の移動はしない）
if move_distance > 0:
    move_forward(move_distance)
else:
    # 移動距離が0以下なら、すでに安全距離内にある（または近すぎる）ため、何もしない
    pass

# ロボットの向きは変更しない（指示通り、向きを変えずに前後移動）
stop(0.5)
