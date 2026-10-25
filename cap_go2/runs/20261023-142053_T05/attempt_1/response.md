# 方針:
#  開始位置・向きを基準に、正方形の4つの角(ウェイポイント)をワールド座標で計算し、
#  「角の方向へ旋回 → 向きを補正しながら直進」を4回くり返して元の場所に戻る。
#  ロボットから見て「前に1m → 左に曲がって1m → …」の左回りの正方形を描く。
#  (開始位置 (0,0)・向き 0 deg なら角は (1,0), (1,1), (0,1), (0,0)。
#   この範囲に箱は無いので衝突しない。最も近い red_box (3,0) とも 2m 離れている)

SIDE = 1.0          # 正方形の1辺 [m]
POS_TOL = 0.05      # 角に到達したとみなす距離 [m]
YAW_TOL = 3.0       # 旋回完了とみなす角度誤差 [deg]
DT = 0.1            # 1回の指令の時間 [s]


def wrap_deg(a):
    # 角度を -180〜180 deg に正規化
    return (a + 180.0) % 360.0 - 180.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def turn_to(target_deg, max_steps=200):
    # 目標の向きとの差が小さくなるまでその場で旋回する(最大 20 秒)
    for _ in range(max_steps):
        err = wrap_deg(target_deg - get_yaw())
        if abs(err) < YAW_TOL:
            break
        rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        if abs(rate) < 0.3:
            rate = math.copysign(0.3, rate)
        walk(0.0, 0.0, rate, duration=DT)


def go_to(tx, ty, max_steps=200):
    # 目標点の方向を向きながら前進する(最大 20 秒)
    # 向きのずれが大きいときは前進を弱め、目標に近づくと減速して行き過ぎを防ぐ
    for _ in range(max_steps):
        x, y = get_position()
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        if dist < POS_TOL:
            break
        heading = math.degrees(math.atan2(dy, dx))
        err = wrap_deg(heading - get_yaw())
        yaw_rate = clamp(2.0 * math.radians(err), -1.0, 1.0)
        speed = clamp(1.0 * dist, 0.15, 0.5)            # 近いほど遅く
        vx = speed * max(0.0, math.cos(math.radians(err)))  # 向きがずれていたら前進を抑える
        walk(vx, 0.0, yaw_rate, duration=DT)


def walk_square():
    x0, y0 = get_position()
    yaw0 = get_yaw()
    c, s = math.cos(math.radians(yaw0)), math.sin(math.radians(yaw0))

    # ロボット基準の角の座標 (前方, 左方) → ワールド座標に変換
    local_corners = [(SIDE, 0.0), (SIDE, SIDE), (0.0, SIDE), (0.0, 0.0)]
    corners = [(x0 + c * fx - s * ly, y0 + s * fx + c * ly) for fx, ly in local_corners]

    print("start: pos=(%.2f, %.2f), yaw=%.1f" % (x0, y0, yaw0))
    for i, (tx, ty) in enumerate(corners):
        x, y = get_position()
        # まず次の角の方向へその場で向き直る(1辺目以外は左に約90度)
        turn_to(math.degrees(math.atan2(ty - y, tx - x)))
        # 角まで直進
        go_to(tx, ty)
        stop(0.3)
        px, py = get_position()
        print("corner %d reached: pos=(%.2f, %.2f), yaw=%.1f" % (i + 1, px, py, get_yaw()))

    # 最後に開始時の向きに戻す
    turn_to(yaw0)
    stop(0.5)
    px, py = get_position()
    print("finish: pos=(%.2f, %.2f), yaw=%.1f, error from start=%.3f m"
          % (px, py, get_yaw(), distance_to(x0, y0)))


walk_square()
