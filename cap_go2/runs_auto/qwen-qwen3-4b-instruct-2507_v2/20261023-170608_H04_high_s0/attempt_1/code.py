# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを確認
current_x, current_y = get_position()
current_yaw = get_yaw()

# ロボットが赤い箱の方向を向くように旋回（face関数で直接向ける）
face(red_box_x, red_box_y)

# 赤い箱まで移動（障害物を避ける必要なし、ただしロボットの大きさを考慮して安全な距離で）
# 到達までの距離を計算
distance = math.hypot(red_box_x - current_x, red_box_y - current_y)

# 安全な距離を確保するために、ロボットの中心が箱の表面に近づかないように調整
# 赤い箱の大きさは 0.3m x 0.3m。ロボットの左右幅は 0.3m、前後は 0.7m。
# よって、ロボットの中心が箱の表面に近づくのは、距離が 0.3m（左右）以下になる場合。
# ここで、安全距離として 0.35m を確保（0.35m はロボットの左右幅の半分 + 0.15m と同程度）。
# つまり、移動距離は、箱までの距離から 0.35m を引いた距離を目標とする。

# よって、目標位置は箱の中心から 0.35m 手前（ロボット側）に設定
target_distance = distance - 0.35
if target_distance < 0:
    target_distance = 0

# 移動を実行（到達まで移動）
reached = move_to(red_box_x - (red_box_x - current_x) / distance * target_distance,
                  red_box_y - (red_box_y - current_y) / distance * target_distance,
                  tolerance=0.15)

print("赤い箱へ到達:", reached)

# 到達後、少し停止
stop(1.0)
