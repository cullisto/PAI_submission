# 指示: 青い箱に寄ってから、緑の箱まで行って。
# 方針: 箱の中心にはぶつかるので、各箱の中心から 0.5 m 手前（ロボット側）を目標にして歩く。
# 経路上（原点→青→緑）に他の箱はないので、直進で問題ない。

def approach(name, margin=0.5, timeout=40.0):
    """物体 name の中心から margin [m] 手前まで歩き、最後に箱の方を向く"""
    bx, by = get_object_position(name)
    x, y = get_position()
    d = math.hypot(bx - x, by - y)
    if d <= margin + 0.05:
        # すでに十分近い
        face(bx, by)
        print(name, "にはすでに近い (距離 %.2f m)" % d)
        return True
    # まず箱の方を向く
    face(bx, by)
    # 箱の中心から margin 手前の点を目標にする
    gx = bx - (bx - x) / d * margin
    gy = by - (by - y) / d * margin
    reached = move_to(gx, gy, tolerance=0.15, timeout=timeout)
    # 到着後、箱の方を向き直す
    face(bx, by)
    px, py = get_position()
    print(name, "到着:", reached, "位置: (%.2f, %.2f)" % (px, py),
          "箱までの距離: %.2f m" % distance_to(bx, by))
    return reached

def main():
    # 1. 青い箱に寄る
    approach("blue_box")
    stop(0.5)
    # 2. 緑の箱まで行く
    approach("green_box")
    stop(0.5)

main()
