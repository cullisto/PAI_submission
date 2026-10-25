# 赤い箱の位置を取得
bx, by = get_object_position("red_box")
x, y = get_position()

# 箱からロボットへ向かう単位ベクトル（箱の「手前側」の方向）
dx, dy = x - bx, y - by
d = math.hypot(dx, dy)
if d < 1e-6:
    dx, dy, d = -1.0, 0.0, 1.0  # 念のため（箱と同じ位置になることはない）
ux, uy = dx / d, dy / d

# 目標地点: 箱の中心から 1.0 m 離れた位置（ロボット側）
# ロボット中心から箱中心まで 1.0 m なら、お尻（後端）と箱表面の間にも十分な余裕がある
TARGET_DIST = 1.0
gx = bx + ux * TARGET_DIST
gy = by + uy * TARGET_DIST
print("目標地点:", (round(gx, 2), round(gy, 2)))

# 目標地点まで歩く（箱の方を向いたまま近づく）
reached = move_to(gx, gy, tolerance=0.1)
print("到着:", reached)

# 箱と反対の方向を向く（＝お尻を箱に向ける）
# 1.0 m 離れていれば、その場旋回しても胴体は箱に当たらない
def face_away_from_box():
    x, y = get_position()
    away_yaw = math.degrees(math.atan2(y - by, x - bx))
    turn_to(away_yaw)

face_away_from_box()

# 距離の誤差を前後移動で補正（お尻が箱側なので、後退すると箱に近づく）
for i in range(3):
    dist = distance_to(bx, by)
    err = dist - TARGET_DIST
    print("補正 %d: 箱までの距離 %.3f m（誤差 %.3f m）" % (i, dist, err))
    if abs(err) < 0.05:
        break
    move_forward(-err)  # 遠すぎれば後退、近すぎれば前進
    face_away_from_box()

stop(0.5)
x, y = get_position()
print("最終位置:", (round(x, 2), round(y, 2)),
      "向き: %.1f deg" % get_yaw(),
      "箱までの距離: %.2f m" % distance_to(bx, by))
