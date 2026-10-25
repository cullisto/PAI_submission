```python
# 前回の失敗は、ロボットが紫の箱の方向に直接移動し、安全距離を確保できず、
# 紫の箱に近づくリスクがある経路を取っていたため、移動中に物体にぶつかり続けた。
# 修正点:
# 1. 紫の箱の位置を避けるため、ロボットが紫の箱の「手前」ではなく、その「横」または「後方」に移動するように経路を設計。
# 2. まずロボットを紫の箱の「y方向の反対側」に移動（例: y 軸の負方向に移動）することで、紫の箱と距離を確保。
# 3. 紫の箱の中心 (2.0, 0.3) からロボットが離れるように、安全な経路を確保。
# 4. 移動中に障害物にぶつからないように、移動前にロボットの向きを調整し、安全な方向に進む。

# 紫の箱と赤い箱の位置を取得
purple_box_x, purple_box_y = get_object_position("purple_box")  # (2.0, 0.3)
red_box_x, red_box_y = get_object_position("red_box")          # (4.5, 0.0)

# ロボットの現在位置と向きを取得
current_x, current_y = get_position()
current_yaw = get_yaw()

# 紫の箱の中心からロボットまでのベクトル
dx = purple_box_x - current_x
dy = purple_box_y - current_y
dist = math.hypot(dx, dy)

# 紫の箱に近づかないように、安全な距離（1.5m）を確保する
safe_distance = 1.5

# 紫の箱の方向にロボットが近づかないように、安全な位置を「紫の箱のy方向の反対側」に設定
# 例: y 軸の負方向に移動することで、紫の箱と距離を確保（紫の箱は (2.0, 0.3) → yが小さい場所に移動）
# 紫の箱の中心から y 軸を下にずらす（安全な位置）
safe_x = current_x + 0.0  # x 方向はほぼそのまま（紫の箱のxに近づかないように、x方向は制限）
safe_y = current_y - 1.0  # y方向に1.0m下にずらす → 紫の箱のy=0.3より下 → 安全

# まず、安全な位置（紫の箱の下）に移動（y方向に移動）
print(f"安全な位置へ移動: ({safe_x:.2f}, {safe_y:.2f})")

# 安全な位置まで移動（安全に距離を確保）
move_to(safe_x, safe_y, tolerance=0.3, timeout=10.0)

# その後、赤い箱に向かって進む（紫の箱に近づかないように、x方向に進む）
# 赤い箱（4.5, 0.0）に向かって、y方向はほぼ0に近づくように進む
reached = move_to(red_box_x, red_box_y, tolerance=0.3, timeout=30.0)
print("赤い箱到着:", reached)

# 到着したら停止
if reached:
    stop(1.0)
```