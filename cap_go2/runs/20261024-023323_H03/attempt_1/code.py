# ===== 方針 =====
# 1. 壁の位置と大きさから隙間の中心 (x=2.0, y≈1.0) を計算する
# 2. 隙間の手前 (x≈1.2) に移動し、+x 方向を向いて横位置を隙間の中心に合わせる
# 3. 向きを保ったまま隙間をまっすぐ通り抜け、壁の向こう側 (x≈3.0) まで進む
# 4. 赤い箱の方を向き、箱の手前（胴体が当たらない距離）まで歩く

# ---- 壁の情報から隙間を計算 ----
objs = {o["name"]: o for o in get_objects()}
wu = objs["wall_upper"]
wl = objs["wall_lower"]

gap_low = wl["y"] + wl["size_y"] / 2.0    # 下側の壁の上端 (≈0.55)
gap_high = wu["y"] - wu["size_y"] / 2.0   # 上側の壁の下端 (≈1.45)
gap_y = (gap_low + gap_high) / 2.0        # 隙間の中心 (≈1.0)
wall_x = wu["x"]                          # 壁の中心 x (=2.0)
wall_half_x = wu["size_x"] / 2.0          # 壁の厚みの半分 (=0.15)
print("隙間: y = %.2f 〜 %.2f, 中心 %.2f" % (gap_low, gap_high, gap_y))

# 胴体の前後半長 0.35 m + 余裕を見て、壁の手前・奥の待機点を決める
before_x = wall_x - wall_half_x - 0.65    # ≈1.2（前端が壁から十分離れる）
after_x = wall_x + wall_half_x + 0.85     # ≈3.0（後端が壁から十分離れる）

# ---- 1. 隙間の手前まで移動 ----
reached = move_to(before_x, gap_y, tolerance=0.1, timeout=20.0)
print("隙間手前に到着:", reached, get_position())

# ---- 2. 正面 (+x) を向いて横位置を補正 ----
turn_to(0)
for i in range(3):
    x, y = get_position()
    err = gap_y - y
    if abs(err) < 0.05:
        break
    move_sideways(err)   # 0 deg を向いているので左(+)= +y
print("通過前の位置:", get_position(), "向き:", get_yaw())

# ---- 3. 隙間をまっすぐ通り抜ける ----
# 隙間の中心線上の点を目標にするので、向きはほぼ +x のまま進む
passed = False
for i in range(3):
    move_to(after_x, gap_y, tolerance=0.15, timeout=15.0)
    x, y = get_position()
    if x > wall_x + wall_half_x + 0.4:   # 後端が壁を抜けた
        passed = True
        break
    # 詰まった場合: 少し下がって横位置を合わせ直して再挑戦
    print("通過に失敗、再試行", i, (x, y))
    move_to(before_x, gap_y, tolerance=0.1, timeout=10.0)
    turn_to(0)
    x, y = get_position()
    if abs(gap_y - y) > 0.05:
        move_sideways(gap_y - y)
print("壁の通過:", passed, get_position())

# ---- 4. 赤い箱の手前まで行く ----
bx, by = get_object_position("red_box")
face(bx, by)
x, y = get_position()
d = math.hypot(bx - x, by - y)
stop_dist = 0.55   # 箱の半幅 0.15 + 胴体前半 0.35 + 余裕 0.05
gx = bx - (bx - x) / d * stop_dist
gy = by - (by - y) / d * stop_dist
reached = move_to(gx, gy, tolerance=0.15, timeout=20.0)
face(bx, by)
print("赤い箱に到着:", reached, "位置:", get_position(), "箱までの距離: %.2f" % distance_to(bx, by))
stop(0.5)
