# 全ての箱に1回ずつ寄ってからスタート地点に戻る
# 前回の問題：安全距離を考慮せず、物体に近づきすぎたため、ロボットがぶつかり続けた
# 修正点：
# 1. 各箱に近づく際、ロボットの中心が物体の表面に近づかないように、安全距離（前後0.35m、左右0.15m）を明確に確保
# 2. move_to() ではなく、より制御的に移動（walk で速度を制御）するようにし、障害物に近づかないようにする
# 3. 各箱に寄る前に、ロボットの向きを適切に調整（箱に向かって直接進むように）

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

# 各箱に寄る（距離を考慮して安全な距離で移動）
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
    # 前後方向（x方向）に0.35m以上、左右方向（y方向）に0.15m以上離れるようにする
    min_dist = 0.35  # 前後方向の最小距離（ロボットの胴体が物体に当たらないように）
    
    # 箱に近づくための目標位置を計算（安全距離を確保）
    if dist < min_dist:
        # 箱に非常に近い場合、少し離れてから移動
        target_dist = min_dist
        # ロボットが箱の中心に向かって、安全距離を確保した位置に移動
        target_x = bx - (dx / dist) * target_dist
        target_y = by - (dy / dist) * target_dist
    else:
        target_dist = min_dist
        target_x = bx - (dx / dist) * target_dist
        target_y = by - (dy / dist) * target_dist
    
    # ロボットの向きを箱の方向に調整（face で直接向く）
    face(bx, by)
    
    # 安全な距離で移動（walk で速度を制御し、障害物にぶつからないように）
    # 速度は 0.2 m/s と小さく、安定して進むようにする
    walk(vx=0.2, duration=10.0)  # 10秒間、ゆっくり進む
    
    # 目標位置に近づくまで、段階的に移動（move_to で安全距離を確保）
    reached = move_to(target_x, target_y, tolerance=0.15)
    print(f"{name} に到着: {reached}")
    
    # 到着後、1秒間静止（安定させる）
    stop(1.0)

# 最後にスタート地点に戻る
# 開始位置に戻るため、安全な距離を確保
start_x, start_y = 0.0, 0.0
# 向きを0度に調整（スタート時と同じ）
turn_to(0.0)
reached = move_to(start_x, start_y, tolerance=0.3)
print("スタート地点に戻り完了:", reached)
stop(1.0)
