# 赤い箱と青い箱の中心位置を取得
rx, ry = get_object_position("red_box")
bx, by = get_object_position("blue_box")

# 2つの箱のちょうど中間の地点を計算（期待値: (2.5, 1.0)）
gx = (rx + bx) / 2.0
gy = (ry + by) / 2.0
print("目標地点:", gx, gy)

# 現在地から目標地点への直線経路が箱にぶつからないか確認
# （箱の大きさ 0.3 m + ロボットの余裕を考慮して、中心から 0.5 m 以内を通るかチェック）
def path_clear(x0, y0, x1, y1, margin=0.5):
    for obj in get_objects():
        ox, oy = obj["x"], obj["y"]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        if L2 < 1e-9:
            continue
        t = max(0.0, min(1.0, ((ox - x0) * dx + (oy - y0) * dy) / L2))
        px, py = x0 + t * dx, y0 + t * dy
        if math.hypot(ox - px, oy - py) < margin:
            print("経路上に近い物体:", obj["name"])
            return False
    return True

x, y = get_position()
print("経路クリア:", path_clear(x, y, gx, gy))

# 目標地点の方を向いてから移動
face(gx, gy)
reached = move_to(gx, gy, tolerance=0.15, timeout=30.0)

# 届かなかった場合は回数制限付きで再試行
attempts = 0
while not reached and attempts < 2:
    attempts += 1
    print("再試行", attempts)
    face(gx, gy)
    reached = move_to(gx, gy, tolerance=0.15, timeout=20.0)

print("到着:", reached, "現在位置:", get_position(),
      "目標までの距離:", distance_to(gx, gy))
stop(0.5)
