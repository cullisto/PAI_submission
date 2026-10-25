# 方針:
# 1. get_objects() で箱を列挙し、現在位置から中心までの距離が最小の箱を選ぶ
#    （初期配置では yellow_box が約 2.24 m で最も近い）
# 2. その場で旋回して箱の方を向く
# 3. 向きを補正しながら前進し、箱の手前（中心から STOP_DIST m）で止まる
#    箱の半幅 0.15 m と Go2 の胴体の半長（約 0.35 m）を考え、0.6 m 手前で止めて衝突を避ける

STOP_DIST = 0.6  # 箱の中心から止まる距離 [m]


def angle_diff(target_deg, current_deg):
    """target - current を -180〜180 deg に正規化して返す"""
    return (target_deg - current_deg + 180.0) % 360.0 - 180.0


def bearing_to(tx, ty):
    """現在位置から点 (tx, ty) への方位 [deg]"""
    x, y = get_position()
    return math.degrees(math.atan2(ty - y, tx - x))


def find_nearest_box():
    boxes = [o for o in get_objects() if "box" in o["name"]]
    if not boxes:
        return None
    nearest = min(boxes, key=lambda o: distance_to(o["x"], o["y"]))
    for o in boxes:
        print(f"{o['name']}: {distance_to(o['x'], o['y']):.2f} m")
    return nearest


def turn_to_face(tx, ty, tol=3.0):
    """点 (tx, ty) の方向を向くまでその場で旋回する"""
    for _ in range(200):  # 最大 20 秒
        err = angle_diff(bearing_to(tx, ty), get_yaw())
        if abs(err) < tol:
            break
        rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)
    stop(0.3)


def go_to(tx, ty, stop_dist):
    """向きを補正しながら前進し、(tx, ty) から stop_dist 以内に入ったら止まる"""
    for _ in range(600):  # 最大 60 秒
        d = distance_to(tx, ty)
        remaining = d - stop_dist
        if remaining <= 0.02:
            break
        err = angle_diff(bearing_to(tx, ty), get_yaw())
        # 大きくずれたら一度その場で向き直す
        if abs(err) > 30.0:
            turn_to_face(tx, ty)
            continue
        yaw_rate = max(-1.0, min(1.0, 1.5 * math.radians(err)))
        # 近づくほど減速して行き過ぎを防ぐ
        vx = max(0.15, min(0.5, 0.8 * remaining))
        walk(vx, 0.0, yaw_rate, duration=0.1)
    stop(0.5)


def main():
    box = find_nearest_box()
    if box is None:
        print("箱が見つかりませんでした")
        return
    tx, ty = box["x"], box["y"]
    print(f"一番近い箱: {box['name']} ({tx:.2f}, {ty:.2f})")

    turn_to_face(tx, ty)
    go_to(tx, ty, STOP_DIST)

    x, y = get_position()
    print(f"到着: 位置 ({x:.2f}, {y:.2f}), 向き {get_yaw():.1f} deg, "
          f"{box['name']} までの距離 {distance_to(tx, ty):.2f} m")


main()
