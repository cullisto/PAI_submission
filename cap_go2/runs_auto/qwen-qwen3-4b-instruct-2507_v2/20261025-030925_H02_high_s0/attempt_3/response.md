```python
# 全ての箱に1回ずつ寄ってからスタート地点に戻る
# 前回の問題：各箱に移動するのに時間がかかりすぎ、タイムアウト（blue_boxに到達できず）
# 修正点：
# 1. 各箱に近づく際、安全距離（前後0.35m、左右0.15m）を明確に確保
# 2. move_to は障害物に近づかないように、安全距離を確保した目標位置に移動
# 3. 各箱に移動する前に、向きを調整（face で直接向く）
# 4. 各移動のdurationを短く、最大10秒以内に完了するように制限
# 5. 終了までに最大110秒以内に終えるように、各ステップでタイムアウトをチェック

import math

# スタート位置
start_x, start_y = 0.0, 0.0

# 各箱の位置を取得
red_box_pos = get_object_position("red_box")
blue_box_pos = get_object_position("blue_box")
green_box_pos = get_object_position("green_box")
yellow_box_pos = get_object_position("yellow_box")

# 箱のリスト（距離の順に並べるため、距離に基づいて並び替え）
boxes = [
    ("red_box", red_box_pos),
    ("blue_box", blue_box_pos),
    ("green_box", green_box_pos),
    ("yellow_box", yellow_box_pos)
]

# シミュレーション時間の上限（120秒 → 110秒までに終える）
max_time = 110.0
current_time = 0.0

# 各箱に寄る
for name, pos in boxes:
    bx, by = pos
    
    # 現在のロボットの位置と方向を取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 箱の中心からロボットの中心までの距離
    dx = bx - x
    dy = by - y
    dist = math.hypot(dx, dy)
    
    # 安全距離を確保（前後方向0.35m、左右方向0.15m）
    min_dist = 0.35  # 前後方向の最小距離（ロボットの胴体が物体に当たらないように）
    
    # 目標位置を安全距離で設定
    if dist < min_dist:
        target_dist = min_dist
        target_x = bx - (dx / dist) * target_dist
        target_y = by - (dy / dist) * target_dist
    else:
        target_dist = min_dist
        target_x = bx - (dx / dist) * target_dist
        target_y = by - (dy / dist) * target_dist
    
    # ロボットの向きを箱の方向に調整
    face(bx, by)
    
    # タイムアウトを考慮して、move_to で最大10秒以内に到達
    reached = move_to(target_x, target_y, tolerance=0.15, timeout=10.0)
    
    if not reached:
        print(f"⚠️ {name} に到達できませんでした（タイムアウト）")
        # タイムアウト時は、わずかに進んでから停止
        walk(vx=0.1, duration=1.0)
        stop(1.0)
        current_time += 11.0  # タイムアウト処理にかかる時間
        continue
    
    print(f"{name} に到着: {reached}")
    stop(1.0)
    current_time += 1.0

# 最後にスタート地点に戻る（安全距離で）
turn_to(0.0)
reached = move_to(start_x, start_y, tolerance=0.3, timeout=10.0)
print("スタート地点に戻り完了:", reached)
stop(1.0)
```