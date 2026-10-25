# 現在の向き（0 deg = +x 方向）のまま 2 m 前進する
# 前方の赤い箱は (3.0, 0.0) にあり、到達点 (2.0, 0.0) からは約 1 m 離れているので衝突しない
start = get_position()
print("開始位置:", start)

move_forward(2.0)

# その場で静止する
stop(1.0)

end = get_position()
print("終了位置:", end, "移動距離:", math.hypot(end[0] - start[0], end[1] - start[1]))
