# 1辺1mの正方形を「前進 → 左に90度旋回」を4回くり返して描き、元の位置・向きに戻る。
# 誤差がたまらないように、各角の座標をワールド座標で計算し、move_to で順番に向かう。
# 経路 (0,0)→(1,0)→(1,1)→(0,1)→(0,0) の近くに箱はないので、ぶつかる心配はない。

side = 1.0  # 正方形の1辺 [m]

# 開始時の位置と向きを記録
sx, sy = get_position()
syaw = get_yaw()
print("開始位置:", (sx, sy), "開始向き:", syaw)

# ロボットから見た「前」と「左」の単位ベクトル（ワールド座標）
th = math.radians(syaw)
fx, fy = math.cos(th), math.sin(th)      # 前方向
lx, ly = -math.sin(th), math.cos(th)     # 左方向

# 正方形の角（前へ1m → 左へ1m → 後ろへ1m → 元の場所）
corners = [
    (sx + fx * side,                sy + fy * side),
    (sx + fx * side + lx * side,    sy + fy * side + ly * side),
    (sx + lx * side,                sy + ly * side),
    (sx,                            sy),
]

for i, (cx, cy) in enumerate(corners):
    face(cx, cy)  # 次の角の方を向く（角で90度左旋回するのと同じ）
    reached = move_to(cx, cy, tolerance=0.1, timeout=20.0)
    px, py = get_position()
    print("角", i + 1, "目標:", (round(cx, 2), round(cy, 2)),
          "現在:", (round(px, 2), round(py, 2)), "到着:", reached)
    stop(0.3)

# 最後に開始時と同じ向きに戻す
turn_to(syaw)
stop(0.5)

px, py = get_position()
print("終了位置:", (round(px, 2), round(py, 2)), "終了向き:", round(get_yaw(), 1))
print("開始位置からのずれ:", round(distance_to(sx, sy), 3), "m")
