# 方針:
# - ロボットは向き 0 deg（+x 方向）を向いたまま、旋回は一切しない。
# - 使う移動は move_sideways（横歩き）と move_forward（前後移動）だけ。
# - 青い箱 (2.0, 2.0) の「手前」= ロボット側（-x 側）から正面で向き合う位置とする。
#   箱の半幅 0.15 m + ロボットの前方半長 0.35 m = 0.5 m で接触するので、
#   少し余裕を持って箱の中心から x 方向に 0.6 m 手前を目標にする。
# - 経路は「先に横歩きで y を合わせる → 前進で x を合わせる」の順。
#   この順なら箱の横をかすめず、正面からまっすぐ近づける。

bx, by = get_object_position("blue_box")
margin = 0.6                     # 箱中心からの距離 [m]
gx, gy = bx - margin, by         # 目標点（箱の手前、正面）
print("青い箱:", (bx, by), "目標:", (gx, gy))


def to_robot_frame(dx, dy):
    """ワールド座標の変位 (dx, dy) をロボット座標（前, 左）に変換する。
    旋回はしないが、歩行中にわずかに向きがずれた場合の補正に使う。"""
    yaw = math.radians(get_yaw())
    fwd = math.cos(yaw) * dx + math.sin(yaw) * dy
    left = -math.sin(yaw) * dx + math.cos(yaw) * dy
    return fwd, left


# 1) 横歩きで y 座標を箱に合わせる（左が正）
x, y = get_position()
_, left = to_robot_frame(gx - x, gy - y)
move_sideways(left)
print("横歩き後:", get_position())

# 2) 前進で箱の手前まで近づく
x, y = get_position()
fwd, _ = to_robot_frame(gx - x, gy - y)
move_forward(fwd)
print("前進後:", get_position())

# 3) 残った誤差を小さく補正（横歩きと前後移動のみ、回数上限付き）
for i in range(3):
    x, y = get_position()
    err = math.hypot(gx - x, gy - y)
    if err < 0.1:
        break
    fwd, left = to_robot_frame(gx - x, gy - y)
    if abs(left) > 0.05:
        move_sideways(left)
    if abs(fwd) > 0.05:
        # 箱にぶつからないよう、前進は目標を越えない範囲に限る
        move_forward(fwd)

stop(0.5)
x, y = get_position()
print("最終位置:", (round(x, 2), round(y, 2)),
      "向き:", round(get_yaw(), 1), "deg",
      "箱までの距離:", round(distance_to(bx, by), 2), "m")
