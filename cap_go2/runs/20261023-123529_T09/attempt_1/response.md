# 方針:
#   前進速度 vx と左回りの旋回角速度 yaw_rate を同時に与えると、半径 r = vx / yaw_rate の円弧を描く。
#   ここでは vx = 0.5 m/s, yaw_rate = 0.5 rad/s で半径 1.0 m の円を左回りに描く。
#   スタート (0,0) で +x を向いているので、円の中心は (0, 1.0)。
#   通る範囲は x: -1.0〜1.0, y: 0.0〜2.0 で、どの箱 (red(3,0), blue(2,2), green(0.5,-2.5), yellow(-2,1)) にも当たらない。
#   短い区間ごとに向きの変化を積算し、合計 360 deg 回ったら終了する（閉ループ）。
#   最後に move_to で開始位置付近へ補正し、元の向き (0 deg) に戻す。

VX = 0.5          # 前進速度 [m/s]
YAW_RATE = 0.5    # 左回りの角速度 [rad/s] -> 半径 1.0 m
DT = 0.5          # 1 区間の時間 [s]
MAX_STEPS = 60    # 安全のための上限（30 秒分。1 周の理論値は約 12.6 秒）


def wrap_deg(a):
    """角度を -180〜180 deg に正規化する。"""
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a


def circle_once():
    start_x, start_y = get_position()
    start_yaw = get_yaw()
    print("開始位置:", (round(start_x, 2), round(start_y, 2)), "向き:", round(start_yaw, 1))

    total_turn = 0.0          # 積算した旋回角 [deg]（左回りが正）
    prev_yaw = start_yaw

    for step in range(MAX_STEPS):
        remaining = 360.0 - total_turn
        if remaining <= 0.0:
            break
        # 残りが少ないときは区間時間を短くして行き過ぎを防ぐ
        remaining_time = math.radians(remaining) / YAW_RATE
        dt = min(DT, max(0.1, remaining_time))

        walk(vx=VX, vy=0.0, yaw_rate=YAW_RATE, duration=dt)

        yaw = get_yaw()
        total_turn += wrap_deg(yaw - prev_yaw)
        prev_yaw = yaw

        if step % 4 == 0:
            x, y = get_position()
            print("step", step, "位置:", (round(x, 2), round(y, 2)),
                  "旋回量:", round(total_turn, 1), "deg")

    stop(0.5)
    x, y = get_position()
    print("一周完了 位置:", (round(x, 2), round(y, 2)),
          "開始点までの距離:", round(distance_to(start_x, start_y), 2), "m")

    # ずれがあれば開始位置付近へ戻る
    if distance_to(start_x, start_y) > 0.2:
        reached = move_to(start_x, start_y, tolerance=0.15, timeout=20.0)
        print("開始位置へ補正:", reached)

    # 元の向きに戻す
    turn_to(start_yaw)
    stop(0.5)
    x, y = get_position()
    print("最終位置:", (round(x, 2), round(y, 2)), "向き:", round(get_yaw(), 1))


circle_once()
