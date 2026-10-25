# 壁を左側（+y 側）から回り込んで、赤い箱の手前まで行く。
# 壁と箱の情報は get_objects() から取得し、経由点を計算する。

ROBOT_HALF_LEN = 0.35    # ロボットの前後方向の半長 [m]
ROBOT_HALF_WIDTH = 0.15  # ロボットの左右方向の半幅 [m]
MARGIN = 0.25            # 安全マージン [m]


def find_object(name):
    for o in get_objects():
        if o["name"] == name:
            return o
    raise ValueError(name)


def go(x, y, tol=0.15, timeout=25.0, retries=2):
    # 経由点へ移動する（失敗したら数回だけ再試行）
    for i in range(retries + 1):
        ok = move_to(x, y, tolerance=tol, timeout=timeout)
        px, py = get_position()
        print("経由点 (%.2f, %.2f) -> 現在 (%.2f, %.2f) 到着=%s" % (x, y, px, py, ok))
        if ok:
            return True
    return False


def main():
    wall = find_object("wall")
    box = find_object("red_box")

    wx, wy = wall["x"], wall["y"]
    w_xmin = wx - wall["size_x"] / 2  # 壁の手前側の面 (x=1.85)
    w_xmax = wx + wall["size_x"] / 2  # 壁の奥側の面 (x=2.15)
    w_ymin = wy - wall["size_y"] / 2  # 壁の右端 (y=-0.8)
    w_ymax = wy + wall["size_y"] / 2  # 壁の左端 (y=+0.8)

    rx, ry = get_position()

    # 回り込む側を決める：ロボットに近い側の壁の端から回る（同じなら左）
    if abs(ry - w_ymax) <= abs(ry - w_ymin):
        side = 1   # 左（+y）側
        pass_y = w_ymax + ROBOT_HALF_LEN + MARGIN   # 旋回しても当たらないよう半長で確保
    else:
        side = -1  # 右（-y）側
        pass_y = w_ymin - ROBOT_HALF_LEN - MARGIN
    print("回り込む側:", "左" if side > 0 else "右", " 通過する y =", round(pass_y, 2))

    # 経由点1: 壁の手前（壁の面から十分離れた x）で、壁の横の y へ
    x_before = w_xmin - ROBOT_HALF_LEN - MARGIN - 0.3   # 約 1.0
    # 経由点2: 壁を通り過ぎた x（壁の奥側の面から十分離れる）
    x_after = w_xmax + ROBOT_HALF_LEN + MARGIN + 0.25   # 約 3.0

    # 箱の手前の最終目標点：箱の中心から (箱の半幅 + ロボット半長 + 少し) 手前
    stop_dist = box["size_x"] / 2 + ROBOT_HALF_LEN + 0.05  # 約 0.55
    goal_x = box["x"] - stop_dist
    goal_y = box["y"]

    # 経由点3: 壁を越えた後、箱と同じ y の列に戻る点（壁と箱の間の空間）
    x_mid = min(x_after, goal_x - 0.3)

    waypoints = [
        (x_before, pass_y),
        (x_after, pass_y),
        (x_mid, goal_y),
    ]

    for (x, y) in waypoints:
        go(x, y)

    # 最後は箱の方を向いて、手前まで直進
    face(box["x"], box["y"])
    reached = go(goal_x, goal_y, tol=0.1, timeout=15.0)
    face(box["x"], box["y"])
    stop(0.5)

    px, py = get_position()
    print("最終位置 (%.2f, %.2f), 箱までの距離 %.2f m, 到着=%s"
          % (px, py, distance_to(box["x"], box["y"]), reached))


main()
