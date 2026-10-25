# 青い箱の位置を取得して、その方に寄る
bx, by = get_object_position("blue_box")
# 現在の位置と青い箱の距離を計算
x, y = get_position()
d = math.hypot(bx - x, by - y)
# 青い箱に近づくための目標位置（箱の中心からロボットの大きさを考慮して0.35m手前）
gx = bx - (bx - x) / d * 0.35
gy = by - (by - y) / d * 0.35
# 青い箱に向かって移動（障害物を避けないが、近づく）
reached_blue = move_to(gx, gy, tolerance=0.3)
print("青い箱に到着:", reached_blue)

# 青い箱に到着したら、緑の箱の位置を取得
gx, gy = get_object_position("green_box")
# 緑の箱に向かって移動（ロボットの大きさを考慮して0.35m手前まで）
d = math.hypot(gx - x, gy - y)
gx_target = gx - (gx - x) / d * 0.35
gy_target = gy - (gy - y) / d * 0.35
reached_green = move_to(gx_target, gy_target, tolerance=0.3)
print("緑の箱に到着:", reached_green)

# 最終的に停止
stop(1.0)
