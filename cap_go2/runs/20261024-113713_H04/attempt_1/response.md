# 方針:
#   赤い箱 (4.2, 0.0) はコの字の奥の壁 wall_back (x=2.85〜3.15, y=-1.35〜1.35) の外側にある。
#   ロボット (0,0) からまっすぐ進むとコの字の内側に入り、奥の壁で行き止まりになる。
#   そこで左の壁 wall_left (x=1.5〜3.15, y=1.05〜1.35) の外側を回り込む。
#     1) (0.8, 1.9)  : コの字の左外側へ出る（壁の外面 y=1.35 から 0.55 m の余裕）
#     2) (3.65, 1.9) : 左の壁・奥の壁の外側に沿って奥へ進む
#     3) (3.65, 0.0) : 奥の壁の裏側を通って箱の正面へ
#        （x=3.65 なら胴体の左右幅 ±0.15 m で 3.5〜3.8。壁の裏面 3.15 と箱の表面 4.05 の間に収まる）
#     4) 箱の方を向いて停止。中心 (3.65, 0) から箱中心まで 0.55 m で、胴体前端は 4.0 m（箱表面 4.05 の手前）。

box_x, box_y = get_object_position("red_box")
STOP_X = box_x - 0.55  # 箱の手前で止まる x 座標

def wrap(a):
    return (a + 180.0) % 360.0 - 180.0

def turn_to(target_yaw, tol=3.0, max_steps=200):
    # 目標の向きまでその場で旋回する
    for _ in range(max_steps):
        err = wrap(target_yaw - get_yaw())
        if abs(err) < tol:
            break
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

def go_to(tx, ty, tol=0.08, max_steps=250):
    # 目標点の方を向きながら前進する（向きのずれが大きいときはその場で旋回）
    for _ in range(max_steps):
        x, y = get_position()
        d = math.hypot(tx - x, ty - y)
        if d < tol:
            return True
        heading = math.degrees(math.atan2(ty - y, tx - x))
        err = wrap(heading - get_yaw())
        if abs(err) > 25.0:
            turn_to(heading, tol=5.0, max_steps=60)
            continue
        vx = max(0.15, min(0.6, 0.8 * d))  # 目標に近づくほど減速
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        walk(vx, 0.0, rate, duration=0.1)
    print("go_to: 上限ステップに到達", (tx, ty), get_position())
    return False

waypoints = [
    (0.8, 1.9),            # コの字の左外側へ
    (STOP_X, 1.9),         # 左の壁の外側に沿って奥へ
    (STOP_X, box_y),       # 奥の壁の裏側を通って箱の正面へ
]

for i, (wx, wy) in enumerate(waypoints):
    go_to(wx, wy)
    print("waypoint", i, "到達:", get_position(), "yaw:", round(get_yaw(), 1))

# 箱の方を向く
x, y = get_position()
turn_to(math.degrees(math.atan2(box_y - y, box_x - x)))
stop(1.0)
print("到着:", get_position(), "箱までの距離:", round(distance_to(box_x, box_y), 2))
