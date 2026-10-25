# 方針: 旋回は一切せず、横歩き(move_sideways)と前後移動(move_forward)だけで移動する。
# ロボットは今 0 deg(+x 方向)を向いているので、「青い箱の手前」は
# ロボットの向きに沿って箱の 0.5 m 手前、つまり箱が真正面に来る位置 (1.5, 2.0) とする。
# 先に左へ横歩きしてから前進する(箱の横をかすめないようにするため)。

bx, by = get_object_position("blue_box")
yaw = math.radians(get_yaw())  # 旋回しないので、この向きはずっと変わらない想定

# 箱の中心から、ロボットの向きと逆方向へ 0.5 m 戻った点を目標にする
# (箱の半幅 0.15 m + 余裕 0.35 m)
APPROACH = 0.5
gx = bx - math.cos(yaw) * APPROACH
gy = by - math.sin(yaw) * APPROACH
print("目標地点:", round(gx, 2), round(gy, 2))

def to_body_frame(dx, dy, yaw_rad):
    """ワールド座標の差分を、ロボットから見た (前方, 左方) の距離に変換する"""
    fwd = dx * math.cos(yaw_rad) + dy * math.sin(yaw_rad)
    side = -dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
    return fwd, side

# 歩行のずれを補正するため、最大 3 回まで「横歩き → 前後移動」を繰り返す
for i in range(3):
    x, y = get_position()
    yaw = math.radians(get_yaw())
    fwd, side = to_body_frame(gx - x, gy - y, yaw)
    print(f"[{i}] 位置=({x:.2f}, {y:.2f}) 前後の残り={fwd:.2f} 横の残り={side:.2f}")
    if abs(fwd) < 0.05 and abs(side) < 0.05:
        break
    # まず横歩きで箱の正面の列に揃える(左が正)
    if abs(side) >= 0.03:
        move_sideways(side)
    # 次に前後移動で箱の手前まで進む(前が正、行き過ぎていれば後退)
    x, y = get_position()
    fwd, side = to_body_frame(gx - x, gy - y, math.radians(get_yaw()))
    if abs(fwd) >= 0.03:
        move_forward(fwd)

stop(0.5)
x, y = get_position()
print("最終位置:", round(x, 2), round(y, 2), "向き:", round(get_yaw(), 1), "deg")
print("箱までの距離:", round(distance_to(bx, by), 2), "m")
