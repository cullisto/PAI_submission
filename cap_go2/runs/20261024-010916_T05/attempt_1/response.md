# 1辺 1 m の正方形を描くように歩き、元の場所・元の向きに戻る。
# 開始位置から「前 1 m → 左 1 m → 後ろ 1 m → 右 1 m」の頂点を左回りに順に回る。
# 経路 (0,0)→(1,0)→(1,1)→(0,1)→(0,0) の近くには箱がないので衝突しない
# （最も近い箱でも経路から 1 m 以上離れている）。

# 開始時の位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()
th = math.radians(yaw0)

# ロボット自身から見た座標 (前, 左) をワールド座標に変換する関数
def to_world(fwd, left):
    wx = x0 + fwd * math.cos(th) - left * math.sin(th)
    wy = y0 + fwd * math.sin(th) + left * math.cos(th)
    return wx, wy

# 正方形の頂点（ロボット基準）: 前 1 m、左前、左、元の位置
corners = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]

for i, (f, l) in enumerate(corners):
    gx, gy = to_world(f, l)
    # 角をきれいに曲がるため、まず次の頂点の方を向いてから歩く
    face(gx, gy)
    reached = move_to(gx, gy, tolerance=0.1, timeout=20.0)
    px, py = get_position()
    print("頂点", i + 1, "目標:", (round(gx, 2), round(gy, 2)),
          "現在:", (round(px, 2), round(py, 2)), "到着:", reached)

# 最後に開始時の向きに戻す
turn_to(yaw0)
px, py = get_position()
print("最終位置:", (round(px, 2), round(py, 2)),
      "開始位置からの距離:", round(distance_to(x0, y0), 3),
      "向き:", round(get_yaw(), 1))
stop(0.5)
