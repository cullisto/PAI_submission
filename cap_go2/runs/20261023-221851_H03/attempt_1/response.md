# ===== 壁と隙間の位置を物体情報から求める =====
objs = {o["name"]: o for o in get_objects()}
wu = objs["wall_upper"]
wl = objs["wall_lower"]

# 壁の x 方向の範囲（手前側・奥側の面）
wall_x_min = min(wu["x"] - wu["size_x"] / 2, wl["x"] - wl["size_x"] / 2)
wall_x_max = max(wu["x"] + wu["size_x"] / 2, wl["x"] + wl["size_x"] / 2)

# 隙間の y 範囲：下側の壁の上端 〜 上側の壁の下端
gap_y_low = wl["y"] + wl["size_y"] / 2    # 0.55
gap_y_high = wu["y"] - wu["size_y"] / 2   # 1.45
gap_y = (gap_y_low + gap_y_high) / 2      # 隙間の中心 1.0
print("隙間: y =", gap_y_low, "〜", gap_y_high, " 中心 y =", gap_y)

# 通過の前後に取る待機点（ロボットの胴長を考えて壁から 0.7 m 程度離す）
pre_x = wall_x_min - 0.7    # 壁の手前
post_x = wall_x_max + 0.7   # 壁の向こう側

bx, by = get_object_position("red_box")


def align_y(target_y, max_iter=3):
    # 向きを +x に保ったまま、横歩きで y を隙間の中心に合わせる
    for _ in range(max_iter):
        _, y = get_position()
        err = target_y - y
        if abs(err) < 0.05:
            break
        turn_to(0)
        move_sideways(err)  # ワールド +y はロボットの左（yaw=0 のとき）


def main():
    # 1. 隙間の正面（壁の手前）まで移動
    ok = move_to(pre_x, gap_y, tolerance=0.1, timeout=20.0)
    print("隙間の手前に到着:", ok, get_position())

    # 2. 壁に対して真っすぐ（+x 方向）を向き、y を隙間の中心に合わせる
    turn_to(0)
    align_y(gap_y)
    turn_to(0)
    print("通過前の位置:", get_position(), "向き:", get_yaw())

    # 3. 隙間を真っすぐ通り抜ける（途中で区切って横ずれを補正）
    for _ in range(3):
        x, _ = get_position()
        remaining = post_x - x
        if remaining < 0.1:
            break
        move_forward(min(remaining, 0.8))
        align_y(gap_y, max_iter=1)
        turn_to(0)
    print("壁を通過:", get_position())

    # 4. 赤い箱の方を向き、箱の手前 0.45 m まで歩く
    face(bx, by)
    x, y = get_position()
    d = math.hypot(bx - x, by - y)
    margin = 0.45
    gx = bx - (bx - x) / d * margin
    gy = by - (by - y) / d * margin
    reached = move_to(gx, gy, tolerance=0.15, timeout=25.0)
    face(bx, by)
    print("赤い箱に到着:", reached, "位置:", get_position(),
          "箱までの距離:", distance_to(bx, by))
    stop(0.5)


main()
