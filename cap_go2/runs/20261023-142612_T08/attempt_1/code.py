# 赤い箱と青い箱の中心座標を取得し、その中点を目標地点にする
rx, ry = get_object_position("red_box")
bx, by = get_object_position("blue_box")
tx, ty = (rx + bx) / 2.0, (ry + by) / 2.0   # 想定では (2.5, 1.0)
print("target:", (tx, ty))

# 障害物チェック: 中点から各箱の中心までは約 1.12 m 離れている。
# 現在地 (0,0) から目標までの直線経路も各箱から 1 m 以上離れているため、直進してよい。

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def go_to(tx, ty, tol=0.08, max_steps=600):  # 最大 60 秒
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < tol:
            print("reached:", (round(x, 3), round(y, 3)))
            return True

        yaw = math.radians(get_yaw())
        # 目標方向をロボット自身の座標系に変換（前方 ex, 左 ey）
        ex = math.cos(yaw) * dx + math.sin(yaw) * dy
        ey = -math.sin(yaw) * dx + math.cos(yaw) * dy

        if dist < 0.4:
            # 近くでは旋回せずに前後・横移動で微調整（目標の周りを回り込まないように）
            vx = clamp(1.2 * ex, -0.3, 0.3)
            vy = clamp(1.2 * ey, -0.3, 0.3)
            walk(vx, vy, 0.0, duration=0.1)
            continue

        # 遠いときは目標の方向を向いてから前進する
        heading_err = math.atan2(ey, ex)  # [rad]
        yaw_rate = clamp(2.0 * heading_err, -1.0, 1.0)
        if abs(heading_err) > math.radians(30):
            # 向きのずれが大きいときはその場で旋回
            if abs(yaw_rate) < 0.3:
                yaw_rate = math.copysign(0.3, yaw_rate)
            walk(0.0, 0.0, yaw_rate, duration=0.1)
        else:
            # 向きを補正しながら前進（近づくほど減速）
            vx = clamp(0.8 * dist, 0.2, 0.8)
            walk(vx, 0.0, yaw_rate, duration=0.1)
    print("timeout: target not reached")
    return False

go_to(tx, ty)
stop(1.0)
x, y = get_position()
print("final position:", (round(x, 3), round(y, 3)), "distance to target:", round(distance_to(tx, ty), 3))
