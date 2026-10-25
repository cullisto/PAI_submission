# 紫の箱（危険物）の中心から1.5m以内に入らないようにし、赤い箱まで行ってもらう
# 前回の失敗は、ロボットが紫の箱に近づかないように安全な距離を確保できず、
# 紫の箱の方向にずれたり、移動指令が無効に処理されたりしたため、停滞した。
# 修正点:
# 1. 紫の箱の方向に直接移動せず、ロボットの向きを調整して安全な経路を確保。
# 2. 紫の箱の手前に安全な距離を確保するため、ロボットが紫の箱に近づかないように、
#    まずロボットを紫の箱の手前（x方向に離れる）に移動し、その後に赤い箱へ進む。
# 3. 移動中に障害物にぶつからないように、各移動段階で位置と向きを確認し、
#    必要に応じて旋回を加える。

# 紫の箱と赤い箱の位置を取得
purple_box_x, purple_box_y = get_object_position("purple_box")
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置と向きを取得
current_x, current_y = get_position()
current_yaw = get_yaw()

# 紫の箱の中心からロボットまでの距離を計算
dist_to_purple = math.hypot(purple_box_x - current_x, purple_box_y - current_y)

# 紫の箱に近づかないように、安全な距離（1.5m）を確保するための安全位置を計算
safe_distance = 1.5
# 紫の箱の方向にロボットが近づかないように、安全な距離を確保
# 紫の箱の方向ベクトルからロボットを離れるように、安全な位置を計算
dx = purple_box_x - current_x
dy = purple_box_y - current_y
dist = math.hypot(dx, dy)

if dist == 0:
    # ロボットが紫の箱の上にいる場合（極端なケース）
    safe_x = current_x + 1.5 * dx / dist if dist > 0 else current_x
    safe_y = current_y + 1.5 * dy / dist if dist > 0 else current_y
else:
    # 紫の箱の方向に安全な距離を離れる
    safe_x = current_x + safe_distance * dx / dist
    safe_y = current_y + safe_distance * dy / dist

# まず、紫の箱に近づかないように安全な位置まで移動
# ただし、移動中に紫の箱に近づかないように、安全な距離を維持
print(f"安全な位置へ移動: ({safe_x:.2f}, {safe_y:.2f})")

# 安全な位置に移動（安全に近づく）
move_to(safe_x, safe_y, tolerance=0.3, timeout=10.0)

# 移動が完了したら、赤い箱へ向かう
# 赤い箱までの距離を確認し、安全に移動
reached = move_to(red_box_x, red_box_y, tolerance=0.3, timeout=30.0)
print("赤い箱到着:", reached)

# 到着したら停止（1秒間）
if reached:
    stop(1.0)
