# 全ての箱に1回ずつ寄ってからスタート地点に戻る
# 各箱に寄るための経路を計画し、ロボットの大きさを考慮して安全な距離を確保

# 物体の情報を取得
objects = get_objects()
red_box_pos = get_object_position("red_box")
blue_box_pos = get_object_position("blue_box")
green_box_pos = get_object_position("green_box")
yellow_box_pos = get_object_position("yellow_box")

# スタート位置
start_x, start_y = 0.0, 0.0

# 各箱に寄る順序を定義（距離の近さ順に並べる）
boxes = [
    ("red_box", red_box_pos),
    ("blue_box", blue_box_pos),
    ("green_box", green_box_pos),
    ("yellow_box", yellow_box_pos)
]

# 各箱に寄る
for name, pos in boxes:
    bx, by = pos
    # ロボットが箱の表面に近づくように、ロボットの中心が物体の表面から離れるように距離を調整
    # 物体の大きさは 0.3m (x, y) なので、ロボットの前後方向に 0.35m、左右に 0.15m の距離を確保
    # よって、ロボットの中心が物体の中心から 0.35m (前後) 以上離れるようにする
    # ただし、物体の中心からロボットの中心までの距離が 0.35m 以上になるように調整
    
    # 箱の中心からロボットの中心までの距離を計算
    dx = bx - start_x
    dy = by - start_y
    dist = math.hypot(dx, dy)
    
    # 箱に近づくための安全距離を確保（ロボットの中心が物体表面に近づかないように）
    # 前後方向（x方向）に 0.35m、左右方向（y方向）に 0.15m 以上離れるようにする
    # よって、距離を 0.35m 以上に保つ
    if dist < 0.35:
        # 箱に近すぎる場合は、少し離れてから寄る
        target_dist = 0.35
        target_x = bx - (bx - start_x) / dist * target_dist
        target_y = by - (by - start_y) / dist * target_dist
    else:
        target_x = bx - (bx - start_x) / dist * 0.35
        target_y = by - (by - start_y) / dist * 0.35
    
    # 箱に向かって移動（安全距離を確保）
    reached = move_to(target_x, target_y, tolerance=0.15)
    print(f"{name} に到着: {reached}")
    
    # 到着後、1秒間静止
    stop(1.0)

# 最後にスタート地点に戻る
# スタート地点に戻るための安全な距離を確保
start_x, start_y = 0.0, 0.0
reached = move_to(start_x, start_y, tolerance=0.3)
print("スタート地点に戻り完了:", reached)
stop(1.0)
