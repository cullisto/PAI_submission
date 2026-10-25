```python
# 全ての箱に1回ずつ寄ってからスタート地点に戻る経路を計画
# 各箱に近づくためには、ロボットの大きさを考慮して、物体の中心からロボットの胴体の境界まで離れるように移動する
# まず、各箱の位置を取得し、ロボットがその箱に近づくまでの距離を計算
# その後、各箱に近づき、その場で止まってから次の箱へ移動
# 最後にスタート地点に戻る

# オブジェクトの情報取得
objects = get_objects()
red_box_pos = get_object_position("red_box")
blue_box_pos = get_object_position("blue_box")
green_box_pos = get_object_position("green_box")
yellow_box_pos = get_object_position("yellow_box")

# ロボットの初期位置と向き
x, y = get_position()
yaw = get_yaw()

# 各箱の中心位置と、ロボットの中心から物体までの安全距離を計算（安全距離はロボットの大きさ分）
# 軸方向の安全距離：前後0.35m、左右0.15m
safe_dist_x = 0.35
safe_dist_y = 0.15

# 各箱の安全距離を考慮した目標位置を設定（物体の中心から安全距離を引く）
target_positions = [
    (red_box_pos[0] - safe_dist_x, red_box_pos[1] - safe_dist_y),
    (blue_box_pos[0] - safe_dist_x, blue_box_pos[1] - safe_dist_y),
    (green_box_pos[0] - safe_dist_x, green_box_pos[1] - safe_dist_y),
    (yellow_box_pos[0] - safe_dist_x, yellow_box_pos[1] - safe_dist_y),
]

# 1つの箱に近づくまで、目標位置に移動する
for target_x, target_y in target_positions:
    # 現在位置と目標位置の距離を計算
    dist_to_target = math.sqrt((target_x - x) ** 2 + (target_y - y) ** 2)
    
    # 距離が0.1m未満なら、すでに近いので止まる
    if dist_to_target < 0.1:
        stop(1.0)
        continue
    
    # 1m以内に到達するまで前進（左右は0）
    for _ in range(300):
        x, y = get_position()
        progress = math.sqrt((target_x - x) ** 2 + (target_y - y) ** 2)
        if progress < 0.1:
            break
        walk(0.5, 0.0, 0.0, duration=0.1)
    stop(1.0)

# すべての箱に寄った後、スタート地点に戻る
# スタート位置に戻るまで、目標位置（0,0）に近づく
start_x, start_y = 0.0, 0.0
for _ in range(300):
    x, y = get_position()
    progress = math.sqrt((start_x - x) ** 2 + (start_y - y) ** 2)
    if progress < 0.1:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(1.0)
```