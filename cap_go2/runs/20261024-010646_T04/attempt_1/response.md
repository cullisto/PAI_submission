# 指示: 青い箱に寄ってから、緑の箱まで行く。
# 方針: 各箱について「現在位置から箱へ向かう直線上で、箱の中心から 0.55 m 手前」を目標にする。
#       （正面から近づくと胴体が当たるのは中心から約 0.5 m なので、少し余裕を持たせる）
# 経路確認: 青い箱(2,2)付近 → 緑の箱(0.5,-2.5) の直線は x≈1.2 付近で y=0 を横切り、
#           赤い箱(3,0)・黄色い箱(-2,1)からは十分離れているので、障害物回避は不要。

CLEARANCE = 0.55  # 箱の中心から止まる距離 [m]


def approach(name, clearance=CLEARANCE, timeout=40.0):
    """箱 name の方を向き、中心から clearance [m] 手前まで歩いて、箱の方を向いて止まる。"""
    bx, by = get_object_position(name)
    x, y = get_position()
    d = math.hypot(bx - x, by - y)
    if d <= clearance + 0.05:
        # すでに十分近い
        print(name, "にはすでに近い (距離 %.2f m)" % d)
        face(bx, by)
        return True

    # 箱の方を向いてから進む
    face(bx, by)

    # 箱の中心から clearance 手前（ロボット側）の点を目標にする
    gx = bx - (bx - x) / d * clearance
    gy = by - (by - y) / d * clearance
    print(name, "へ移動: 目標 (%.2f, %.2f)" % (gx, gy))
    reached = move_to(gx, gy, tolerance=0.15, timeout=timeout)

    # 到着後、箱の方を向き直す
    face(bx, by)
    px, py = get_position()
    print(name, "到着:", reached, "現在位置 (%.2f, %.2f), 箱まで %.2f m"
          % (px, py, distance_to(bx, by)))
    return reached


def main():
    # 1) 青い箱に寄る
    approach("blue_box")
    stop(1.0)  # 寄ったことがわかるように少し止まる

    # 2) 緑の箱まで行く
    approach("green_box")
    stop(0.5)


main()
