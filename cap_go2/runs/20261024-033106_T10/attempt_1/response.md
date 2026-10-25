# 方針:
#   壁 (中心 (2.0, 0.0), 大きさ 0.3 x 1.6) は x: 1.85〜2.15, y: -0.8〜0.8 を占める。
#   ロボットは前後 0.7 m なので、どの向きでも壁から 0.35 m 以上 + 余裕 0.3 m 離れた
#   経由点を通って壁の横を回り込み、最後に赤い箱の手前 (-x 側) で止まる。
#   各経由点へは「目標方向を向く → 向きを補正しながら前進」の単純な制御で移動する。

def angle_diff(a, b):
    """a - b を -180〜180 deg に正規化して返す"""
    return (a - b + 180.0) % 360.0 - 180.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def go_to(tx, ty, tol=0.12, max_steps=400):
    """点 (tx, ty) まで移動する。到達したら True。max_steps * 0.1 秒で打ち切り"""
    for _ in range(max_steps):
        x, y = get_position()
        d = math.hypot(tx - x, ty - y)
        if d < tol:
            return True
        target_yaw = math.degrees(math.atan2(ty - y, tx - x))
        err = angle_diff(target_yaw, get_yaw())
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(err) > 25.0:
            # 向きが大きくずれているときはその場で旋回
            if abs(rate) < 0.3:
                rate = math.copysign(0.3, rate)
            walk(0.0, 0.0, rate, duration=0.1)
        else:
            # 向きを補正しながら前進（近づくほど減速）
            v = clamp(0.8 * d, 0.15, 0.6)
            walk(v, 0.0, rate, duration=0.1)
    print("go_to timeout:", (tx, ty), get_position())
    return False


def turn_to(target_yaw, tol=3.0, max_steps=150):
    """指定の向き [deg] までその場で旋回する"""
    for _ in range(max_steps):
        err = angle_diff(target_yaw, get_yaw())
        if abs(err) < tol:
            return
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)


def main():
    # 物体情報を取得
    objs = {o["name"]: o for o in get_objects()}
    wall = objs["wall"]
    box = objs["red_box"]

    w_xmin = wall["x"] - wall["size_x"] / 2.0
    w_xmax = wall["x"] + wall["size_x"] / 2.0
    w_ymin = wall["y"] - wall["size_y"] / 2.0
    w_ymax = wall["y"] + wall["size_y"] / 2.0

    # 壁との距離: 胴体の半分の長さ 0.35 m + 余裕 0.3 m
    clearance = 0.35 + 0.3

    # 回り込む側を決める（ロボットが壁の中心より左側(または真正面)なら左 (+y) から回る）
    rx, ry = get_position()
    if ry >= wall["y"]:
        side_y = w_ymax + clearance
    else:
        side_y = w_ymin - clearance

    # 経由点: 壁の手前の横 → 壁の奥の横
    waypoints = [
        (w_xmin - clearance, side_y),
        (w_xmax + clearance, side_y),
    ]

    # 最終目標: 箱の手前 (-x 側)。箱の半分 0.15 + 胴体前半分 0.35 + 余裕 0.1
    stop_dist = box["size_x"] / 2.0 + 0.35 + 0.1
    goal = (box["x"] - stop_dist, box["y"])

    for wx, wy in waypoints:
        print("waypoint:", (round(wx, 2), round(wy, 2)))
        go_to(wx, wy, tol=0.15)

    print("goal:", (round(goal[0], 2), round(goal[1], 2)))
    go_to(goal[0], goal[1], tol=0.08)
    stop(0.3)

    # 最後に箱の方を向く
    x, y = get_position()
    turn_to(math.degrees(math.atan2(box["y"] - y, box["x"] - x)))
    stop(1.0)

    x, y = get_position()
    print("final position:", (round(x, 2), round(y, 2)),
          "yaw:", round(get_yaw(), 1),
          "dist to box:", round(distance_to(box["x"], box["y"]), 2))


main()
