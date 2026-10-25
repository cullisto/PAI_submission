# 方針:
#  1) 青い箱 (2.0, 2.0) の方を向いて前進し、箱の手前（中心から約 0.6 m）で止まる
#     ※ 箱の半幅 0.15 m + ロボット前後半長 0.35 m = 0.5 m が接触距離なので、余裕を持って 0.6 m
#  2) 少し静止して「寄った」ことを示す
#  3) 緑の箱 (0.5, -2.5) の方を向いて同様に前進し、手前で止まる
#  経路確認: (0,0)→青、青付近→緑 の直線はいずれも赤い箱 (3,0) や黄色い箱 (-2,1) から十分離れている

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def angle_err(target_deg):
    # 目標方位と現在の向きの差 [deg]（-180〜180）
    return (target_deg - get_yaw() + 180.0) % 360.0 - 180.0

def bearing_to(tx, ty):
    x, y = get_position()
    return math.degrees(math.atan2(ty - y, tx - x))

def turn_to(target_deg, tol=3.0, max_steps=200):
    # その場旋回で目標方位を向く
    for _ in range(max_steps):
        err = angle_err(target_deg)
        if abs(err) < tol:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=0.1)
    stop(0.3)

def go_near(name, stop_dist=0.6, max_steps=400):
    tx, ty = get_object_position(name)
    print("目標:", name, (tx, ty))
    # まず目標の方を向く
    turn_to(bearing_to(tx, ty))
    # 向きを補正しながら前進
    for _ in range(max_steps):  # 最大 40 秒
        d = distance_to(tx, ty)
        if d <= stop_dist:
            break
        err = angle_err(bearing_to(tx, ty))
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(err) > 30.0:
            vx = 0.0  # 大きくずれていたら旋回を優先
        else:
            # 近づくほど減速、向きのずれに応じても減速
            vx = clamp(0.8 * (d - stop_dist) + 0.15, 0.15, 0.7) * math.cos(math.radians(err))
        walk(vx, 0.0, rate, duration=0.1)
    stop(0.5)
    print(name, "に到着: 位置", get_position(), "距離", round(distance_to(tx, ty), 2))

def main():
    # 1) 青い箱に寄る
    go_near("blue_box", stop_dist=0.6)
    # 2) 寄ったことを示すために少し止まる
    stop(1.0)
    # 3) 緑の箱まで行く
    go_near("green_box", stop_dist=0.6)
    stop(0.5)

main()
