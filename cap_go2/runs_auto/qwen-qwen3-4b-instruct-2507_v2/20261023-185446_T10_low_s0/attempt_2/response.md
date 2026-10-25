```python
# 壁にぶつからないように避けて、赤い箱まで行っていく（修正版）
# 前回は移動速度が小さすぎたり、壁との距離判断が不十分だったため、
# 1. 目標点への進む速度を明確に設定（安全な速度で直進）
# 2. 壁に近づかないように、常に安全距離を確保する
# 3. 壁の左右にずれるようにする（壁に平行に進むようにする）

import math

# 初期位置と向きを記録
x0, y0 = get_position()
current_yaw = get_yaw()

# 赤い箱と壁の位置を取得
red_box_pos = get_object_position("red_box")
wall_pos = get_object_position("wall")

target_x, target_y = red_box_pos
wall_x, wall_y = wall_pos
wall_size_x, wall_size_y = 0.3, 1.6

# ロボットのサイズ（胴体中心から）
robot_length = 0.7  # 前後
robot_width = 0.3   # 左右

# 安全距離：壁に近づかないように、左右方向に 0.15m より近づかない
safe_margin_y = 0.15  # y 方向（左右）

# 壁の y 方向範囲：(wall_y - wall_size_y/2, wall_y + wall_size_y/2)
wall_y_min = wall_y - wall_size_y / 2
wall_y_max = wall_y + wall_size_y / 2

# 最大試行回数（120秒以内に終了）
max_steps = 1000
for step in range(max_steps):
    # 現在の位置と向きを取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 赤い箱までの距離
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.sqrt(dx*dx + dy*dy)
    
    # 距離が小さければ、ゴールに近づくようにゆっくりと動く
    if distance_to_target < 0.3:
        # 0.5m/s で直進（安全に近づく）
        vx = 0.5
        vy = 0.0
    else:
        # ターゲット方向に進む
        # より安全に進むために、目標点への単位ベクトルで速度を設定
        target_dir_x = dx / distance_to_target
        target_dir_y = dy / distance_to_target
        vx = 0.5 * target_dir_x
        vy = 0.5 * target_dir_y
    
    # 壁との距離をチェック（y 方向に近づかないように）
    # ロボットの中心が壁の y 方向範囲内に入らないようにする
    if (y < wall_y_min + safe_margin_y) or (y > wall_y_max - safe_margin_y):
        # 壁に近づいている → y 方向にずらす（壁に平行に進む）
        # 壁の中心 y に近づくように
        if y < wall_y:
            vy = 0.3
        else:
            vy = -0.3
        # 前後速度を 0 に抑える（y 方向のみ移動）
        vx = 0.0
    else:
        # 壁に近づいていない → 直進
        pass
    
    # 速度を範囲内に収める
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # 旋回は不要（直進のみ）
    yaw_rate = 0.0
    
    # 0.1秒間歩く（小さいステップで安全に移動）
    walk(vx, vy, yaw_rate, duration=0.1)
    
    # 10ステップごとに位置を確認（安全確認）
    if step % 10 == 0:
        current_x, current_y = get_position()
        print(f"ステップ {step}: 位置 ({current_x:.2f}, {current_y:.2f}), 向き {current_yaw:.1f} deg")

# ゴールに到達したら、1秒間止まる
stop(1.0)
```