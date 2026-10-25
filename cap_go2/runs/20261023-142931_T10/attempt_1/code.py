# 方針:
#   壁 (中心 (2.0, 0.0), 大きさ 0.3 x 1.6) は x: 1.85〜2.15, y: -0.8〜0.8 を占める。
#   左側 (y = +1.4) を回り込む経路で、ウェイポイントを順にたどって赤い箱へ向かう。
#   ・(1.2, 1.4) : 壁の手前で左へ寄る
#   ・(2.8, 1.4) : 壁の横を通過（壁の端 y=0.8 から 0.6 m の余裕）
#   ・赤い箱の手前 0.5 m で停止し、箱の方を向く
#   API で取得した物体情報から壁の範囲を計算し、回避側の y を決める。

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def angle_diff_deg(target, current):
    # target - current を -180〜180 deg に正規化
    return (target - current + 180.0) % 360.0 - 180.0

def turn_to(target_yaw, max_steps=150):
    # その場で目標の向きまで旋回する
    for _ in range(max_steps):
        err = angle_diff_deg(target_yaw, get_yaw())
        if abs(err) < 3.0:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)

def go_to(tx, ty, tol=0.2, speed=0.6, max_steps=300):
    # 目標点の方向を向きながら前進する（向きのずれが大きいときは旋回を優先）
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            return True
        desired = math.degrees(math.atan2(dy, dx))
        err = angle_diff_deg(desired, get_yaw())
        yaw_rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(err) > 45.0:
            vx = 0.0                      # 大きくずれていればその場旋回
        elif abs(err) > 20.0:
            vx = 0.2                      # 中程度のずれはゆっくり前進
        else:
            vx = min(speed, 0.5 + dist)   # ほぼ正面なら前進
        walk(vx, 0.0, yaw_rate, duration=0.1)
    print("go_to: 目標に到達できず", (tx, ty))
    return False

def main():
    # 物体情報の取得
    box_x, box_y = get_object_position("red_box")
    wall = None
    for obj in get_objects():
        if obj["name"] == "wall":
            wall = obj
    if wall is None:
        wall = {"x": 2.0, "y": 0.0, "size_x": 0.3, "size_y": 1.6}

    # 壁の占める範囲
    wall_x_min = wall["x"] - wall["size_x"] / 2.0
    wall_x_max = wall["x"] + wall["size_x"] / 2.0
    wall_y_max = wall["y"] + wall["size_y"] / 2.0

    # 回避用の経路（壁の左側を、端から 0.6 m 離れて通る）
    margin = 0.6
    side_y = wall_y_max + margin
    waypoints = [
        (wall_x_min - 0.65, side_y),   # 壁の手前で左に寄る
        (wall_x_max + 0.65, side_y),   # 壁の横を通り抜ける
    ]
    print("経路:", waypoints)

    for wx, wy in waypoints:
        go_to(wx, wy, tol=0.2)
        print("通過:", get_position())

    # 赤い箱の手前 0.5 m まで近づく（箱自体にはぶつからない）
    for _ in range(300):
        if distance_to(box_x, box_y) <= 0.5:
            break
        x, y = get_position()
        desired = math.degrees(math.atan2(box_y - y, box_x - x))
        err = angle_diff_deg(desired, get_yaw())
        yaw_rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        vx = 0.0 if abs(err) > 45.0 else (0.2 if abs(err) > 20.0 else 0.4)
        walk(vx, 0.0, yaw_rate, duration=0.1)
    stop(0.3)

    # 箱の方を向いて停止
    x, y = get_position()
    turn_to(math.degrees(math.atan2(box_y - y, box_x - x)))
    stop(1.0)
    print("到着:", get_position(), "向き:", get_yaw(),
          "箱までの距離:", distance_to(box_x, box_y))

main()
