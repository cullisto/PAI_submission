# 赤い箱と青い箱の中心位置を取得
rx, ry = get_object_position("red_box")
bx, by = get_object_position("blue_box")

# 2つの箱のちょうど中間の地点（中点）を計算する
# 赤 (3.0, 0.0) と青 (2.0, 2.0) の中点は (2.5, 1.0)
mx = (rx + bx) / 2.0
my = (ry + by) / 2.0
print("目標の中間地点:", (mx, my))

# 中間地点は各箱の中心から約 1.12 m 離れているので、箱に接触せずに到達できる。
# 現在地 (0, 0) から中間地点への直線経路も、各箱から約 1.1 m 離れているので衝突しない。

# 中間地点へ移動する（ちょうど中間に着きたいので、許容誤差は小さめにする）
reached = move_to(mx, my, tolerance=0.1, timeout=30.0)
print("到着:", reached)

# 到着しなかった場合は、もう一度だけ試す
if not reached:
    reached = move_to(mx, my, tolerance=0.15, timeout=20.0)
    print("再試行の結果:", reached)

# 到着後の位置と、中間地点までの残りの距離を確認
x, y = get_position()
print("現在位置:", (round(x, 2), round(y, 2)), "中間地点までの距離:", round(distance_to(mx, my), 2))

stop(0.5)
