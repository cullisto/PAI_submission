# 今の向き（0 deg = +x 方向）のまま 2 m 前進する
start_x, start_y = get_position()
move_forward(2.0)

# その場で静止する
stop(1.0)

# 結果を確認
x, y = get_position()
print("開始位置:", (start_x, start_y))
print("現在位置:", (x, y))
print("移動距離:", math.hypot(x - start_x, y - start_y))
