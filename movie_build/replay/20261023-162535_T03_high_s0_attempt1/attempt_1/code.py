# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")
# ロボットが現在の位置から赤い箱の中心に向かって移動する
reached = move_to(red_box_x, red_box_y, tolerance=0.3)
print("赤い箱まで到達:", reached)
if reached:
    stop(1.0)
