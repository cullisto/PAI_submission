```python
# 全ての箱に1回ずつ寄ってからスタート地点に戻る経路を、より効率的に計画
# 前回の失敗は、各箱に近づくために無駄な移動を繰り返していたため、各目標に到達するまでの移動を明確に制御
# 各箱の安全距離を考慮し、最も近い経路で移動。方向を常に目標に向かって調整
# すべての移動を短時間で行い、時間切れを防ぐために、最大30回のループで移動を制限

# オブジェクトの位置を取得
red_box_pos = get_object_position("red_box")
blue_box_pos = get_object_position("blue_box")
green_box_pos = get_object_position("green_box")
yellow_box_pos = get_object_position("yellow_box")

# ロボットの初期位置と向き
x, y = get_position()
yaw = get_yaw()

# 各箱の安全距離（ロボットの胴体の境界）
safe_dist_x = 0.35  # 前後
safe_dist_y = 0.15  # 左右

# 各箱の安全距離を考慮した目標位置（物体中心からロボットが当たらないように）
target_positions = [
    (red_box_pos[0] - safe_dist_x, red_box_pos[1] - safe_dist_y),
    (blue_box_pos[0] - safe_dist_x, blue_box_pos[1] - safe_dist_y),
    (green_box_pos[0] - safe_dist_x, green_box_pos[1] - safe_dist_y),
    (yellow_box_pos[0] - safe_dist_x, yellow_box_pos[1] - safe_dist_y),
]

# 各目標に近づく（最大30回のループで制御）
for target_x, target_y in target_positions:
    # 現在の位置から目標までの距離を計算
    dx = target_x - x
    dy = target_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    # 距離が0.1m以下なら、すでに近い → 停止
    if dist < 0.1:
        stop(0.5)
        continue
    
    # 10ステップで最大移動（0.5m/sで1ステップ0.1秒 → 最大0.5m）
    for step in range(30):
        # 現在の位置を更新
        x, y = get_position()
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 0.1m以内なら終了
        if dist < 0.1:
            break
            
        # 方向を目標に合わせて前進（左右は0）
        walk(0.5, 0.0, 0.0, duration=0.1)
    stop(0.5)

# すべての箱に寄った後、スタート地点に戻る（最大30ステップ）
start_x, start_y = 0.0, 0.0
for step in range(30):
    x, y = get_position()
    dx = start_x - x
    dy = start_y - y
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist < 0.1:
        break
        
    walk(0.5, 0.0, 0.0, duration=0.1)
stop(1.0)
```