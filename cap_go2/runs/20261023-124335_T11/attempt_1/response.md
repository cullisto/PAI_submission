# 赤い箱（ゴール）と壁（障害物）の情報を取得
gx, gy = get_object_position("red_box")
wall = None
for obj in get_objects():
    if obj["name"] == "wall":
        wall = obj
        break

MARGIN = 0.5      # 壁からとる余裕 [m]（ロボットの胴体の大きさを考慮）
STOP_DIST = 0.5   # 箱の中心から手前で止まる距離 [m]

rx, ry = get_position()

# 壁が箱への直線経路をふさいでいる場合は迂回する
if wall is not None:
    wx, wy = wall["x"], wall["y"]
    half_x, half_y = wall["size_x"] / 2, wall["size_y"] / 2

    # 迂回する側を決める（ロボットが壁の中心より右にいれば右、それ以外は左）
    side = -1.0 if ry < wy else 1.0
    detour_y = wy + side * (half_y + MARGIN)

    # 経由点1: 壁の手前で横にずれた位置
    p1 = (wx - half_x - MARGIN, detour_y)
    # 経由点2: 壁を越えた先の同じ横位置
    p2 = (wx + half_x + MARGIN, detour_y)

    for i, (px, py) in enumerate([p1, p2]):
        ok = move_to(px, py, tolerance=0.15, timeout=20.0)
        print("経由点", i + 1, (round(px, 2), round(py, 2)), "到着:", ok)

# 箱の手前（ロボット側）STOP_DIST の位置を最終目標にする
x, y = get_position()
d = math.hypot(gx - x, gy - y)
if d > STOP_DIST:
    tx = gx - (gx - x) / d * STOP_DIST
    ty = gy - (gy - y) / d * STOP_DIST
    reached = move_to(tx, ty, tolerance=0.15, timeout=20.0)
    print("赤い箱の手前に到着:", reached)

# 最後に箱の方を向いて止まる
face(gx, gy)
stop(0.5)
print("最終位置:", get_position(), "箱までの距離:", round(distance_to(gx, gy), 2))
