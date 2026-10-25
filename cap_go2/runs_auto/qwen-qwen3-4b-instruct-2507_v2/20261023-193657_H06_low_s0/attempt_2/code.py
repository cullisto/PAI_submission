# 赤い箱にお尻を向けて、箱から1メートル離れた位置で止まることを達成する
# 原因の分析: 
# 1. 赤い箱までの距離が2.14m（基準0.75〜1.25m）→ 遠すぎる。移動中に障害物にぶつからないように、正確な距離管理が必要。
# 2. お尻の向きのずれが180deg（基準<25deg）→ 向きがまったく間違っている。赤い箱の中心に対して後ろを向くように正確に制御。

# 赤い箱の中心座標を取得
red_box_x, red_box_y = get_object_position("red_box")

# 目標位置: 赤い箱の中心からロボットの「後ろ」に1m離れた点（お尻を向ける）
# ロボットの向きは赤い箱の中心に対して180度（後ろ）になるようにする

# 初期位置と向きを取得
x, y = get_position()
yaw = get_yaw()

# 赤い箱の中心からロボットの中心へのベクトル
dx = red_box_x - x
dy = red_box_y - y
distance_to_box = math.sqrt(dx**2 + dy**2)

# 距離が1.25mを超える場合は、まず近づく（距離を0.75〜1.25mの範囲に制限）
# 1.25m以内に近づくまで前進（前方を向いて、赤い箱に向かって進む）
# ただし、距離が0.75m以下になる場合は、後ろに1m離れた位置に移動する準備

# 距離が1.25mを超える場合、近づく（目標距離を1.25mに制限）
target_distance = 1.25
if distance_to_box > target_distance:
    # 赤い箱に向かって進む（前方を向いて）
    # 方向ベクトルを単位化
    if distance_to_box > 0:
        dir_x = dx / distance_to_box
        dir_y = dy / distance_to_box
        # 1.25mまで進む（距離を制御）
        for _ in range(300):
            x, y = get_position()
            dist = math.sqrt((red_box_x - x)**2 + (red_box_y - y)**2)
            if dist <= target_distance:
                break
            walk(0.5, 0.0, 0.0, duration=0.1)
else:
    # すでに1.25m以内なら、次のステップへ（向きを調整）

# お尻を向ける（赤い箱の中心に対して180度）
target_yaw = (math.degrees(math.atan2(red_box_y - y, red_box_x - x)) + 180.0) % 360.0

# 向きが目標に達するまで右回り（負の角速度）で旋回
for _ in range(300):  # 最大30秒
    current_yaw = get_yaw()
    # より安定した差分計算（-180〜180度）
    yaw_diff = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
    if abs(yaw_diff) < 5.0:  # 5度以内に達したら終了
        break
    rate = max(-1.0, min(1.0, -2.0 * math.radians(yaw_diff)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.1)

# お尻を向けて、赤い箱の中心から1m離れた位置に到達
# 1m離れた位置は、ロボットの向き（後ろ）に1m離れた点
# ロボットの現在の位置から、後ろ方向に1m進む
current_x, current_y = get_position()
current_yaw = get_yaw()

# 向きから後ろ方向の単位ベクトルを計算（後ろを向く方向）
# つまり、赤い箱の中心方向に反対方向
dx = red_box_x - current_x
dy = red_box_y - current_y
distance = math.sqrt(dx**2 + dy**2)
if distance > 0:
    dir_x = -dx / distance
    dir_y = -dy / distance
else:
    dir_x, dir_y = 0.0, 0.0

# 後ろに1m進む
target_x = current_x + dir_x * 1.0
target_y = current_y + dir_y * 1.0

# 1m離れた位置に到達するまで移動（後ろを向いて、1m進む）
for _ in range(300):
    x, y = get_position()
    dist = math.sqrt((target_x - x)**2 + (target_y - y)**2)
    if dist <= 0.2:  # 0.2m以内に達したら終了
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(0.5)
