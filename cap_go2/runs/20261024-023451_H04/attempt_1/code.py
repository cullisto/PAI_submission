# 赤い箱はコの字形の壁の「奥の壁の外側」にあるため、まっすぐ進むと wall_back にぶつかる。
# 右側の壁 (wall_right) の外側を回り込んでから、箱の手前（-y 側）に近づく。
#
# 壁の範囲（中心±大きさ/2）:
#   wall_back : x 2.85〜3.15, y -1.35〜1.35
#   wall_right: x 1.50〜3.15, y -1.35〜-1.05
# 迂回ルートは y = -1.9 とする（壁の外面 y=-1.35 から 0.55 m 離れ、ロボット半幅 0.15 m に十分な余裕）。

bx, by = get_object_position("red_box")  # (4.2, 0.0)
box_half = 0.15        # 箱の半分の大きさ
robot_half_len = 0.35  # ロボット前後方向の半分の長さ
margin = 0.1           # 箱との余裕

DETOUR_Y = -1.9

# 経由点: 壁の手前で右に出る → 壁の外側を前進 → 箱の真横（-y 側）まで
waypoints = [
    (1.0, DETOUR_Y),  # wall_right の始点 (x=1.5) より手前で右に回り込む
    (bx, DETOUR_Y),   # 壁を越えて箱の x 座標まで（x=4.2 は壁の端 3.15 より十分先）
]

def go(x, y, tol, timeout):
    face(x, y)  # 先に目標の方向を向いてから直進（大きく膨らまないように）
    ok = move_to(x, y, tolerance=tol, timeout=timeout)
    px, py = get_position()
    print("目標 (%.2f, %.2f) 到着: %s 現在位置 (%.2f, %.2f)" % (x, y, ok, px, py))
    return ok

def main():
    for (wx, wy) in waypoints:
        go(wx, wy, 0.2, 40.0)

    # 箱の -y 側から +y 方向に近づく。
    # 箱の表面 (by - 0.15) からロボットの前後半長 0.35 + 余裕 0.1 → 箱中心から 0.6 m 手前
    gx = bx
    gy = by - (box_half + robot_half_len + margin)
    go(gx, gy, 0.1, 25.0)

    # 最後に箱の方を向いて停止
    face(bx, by)
    stop(0.5)
    print("赤い箱までの距離: %.2f m" % distance_to(bx, by))

main()
