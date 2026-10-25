# 方針:
# - 指示どおり旋回は一切しない（yaw_rate は常に 0）。前後(vx)と横歩き(vy)だけで移動する。
# - ロボットは +x 方向（0 deg）を向いたまま。「青い箱の手前」は、箱の -x 側（ロボットから見て箱が正面に来る位置）とする。
# - Go2 の体長は約 0.7 m（中心から鼻先まで約 0.35 m）、箱の半幅は 0.15 m なので、
#   ロボット中心が箱中心から 0.6 m 手前に来るように止める（鼻先と箱の間に約 0.1 m の余裕）。
# - 経路 (0,0)→(1.4,2.0) 上に他の箱はない（赤 (3,0)、緑 (0.5,-2.5)、黄 (-2,1) はいずれも離れている）。

bx, by = get_object_position("blue_box")
STANDOFF = 0.6                       # 箱中心からロボット中心までの距離 [m]
tx, ty = bx - STANDOFF, by           # 目標位置（箱の -x 側＝ロボットから見て手前）
print(f"target: ({tx:.2f}, {ty:.2f})")

TOL = 0.05        # 到達判定 [m]
V_MAX = 0.5       # 移動速度の上限 [m/s]（vy の範囲 ±0.5 に合わせる）
V_MIN = 0.1       # 目標近くで止まりきらないための最小速度 [m/s]
KP = 1.0          # 比例ゲイン

for i in range(400):  # 最大 40 秒
    x, y = get_position()
    ex, ey = tx - x, ty - y
    dist = math.hypot(ex, ey)
    if dist < TOL:
        break

    # ワールド座標の誤差をロボット座標系に変換（向きが多少ずれても正しく補正できるよう現在の yaw を使う）
    yaw = math.radians(get_yaw())
    ex_b = math.cos(yaw) * ex + math.sin(yaw) * ey    # 前方成分
    ey_b = -math.sin(yaw) * ex + math.cos(yaw) * ey   # 左方成分

    # 速さを比例制御で決め、方向を保ったまま上下限でクリップする
    speed = max(V_MIN, min(V_MAX, KP * dist))
    vx = speed * ex_b / dist
    vy = speed * ey_b / dist

    walk(vx, vy, 0.0, duration=0.1)   # yaw_rate = 0（旋回しない）

    if i % 10 == 0:
        print(f"pos=({x:.2f}, {y:.2f}) yaw={math.degrees(yaw):.1f} dist={dist:.2f}")

stop(1.0)
x, y = get_position()
print(f"final pos=({x:.2f}, {y:.2f}), yaw={get_yaw():.1f} deg, "
      f"distance to blue_box={distance_to(bx, by):.2f} m")
