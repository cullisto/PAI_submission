```python
# 壁にぶつからないように避けて、赤い箱まで行っていく（最終修正版）
# 前回の問題点：
# - 壁に近づくと y 方向の速度が大きくなりすぎ、ロボットが壁に押し付けられ続けた
# - 壁の y 方向範囲に近づくと、ずらす処理が効いていない（y 方向の安全距離が常に満たされず）
# - 動きが止まっているのは、壁に近づいていても「安全距離」の判定が遅れていたため
# 
# 修正点：
# 1. 壁に近づくかどうかを、常にロボットの中心が壁の y 方向範囲内に入らないようにする
# 2. 壁に近づくと、y 方向にずらすが、そのずらしは「安全距離を維持する」ようにする
# 3. 前後速度を常に 0.5 以下に保ち、壁に近づくと y 方向のみに移動するようにする
# 4. 動きが止まらないように、ループ内で常に進むようにする（安全距離を満たすまで）

import math

# 赤い箱と壁の情報
red_box_pos = get_object_position("red_box")
wall_pos = get_object_position("wall")
target_x, target_y = red_box_pos
wall_x, wall_y = wall_pos
wall_size_x, wall_size_y = 0.3, 1.6

# ロボットのサイズ（胴体中心から）
robot_width = 0.3  # 左右幅 → y 方向に 0.15m より近づかない
safe_margin_y = 0.15  # y 方向の安全距離

# 壁の y 方向範囲
wall_y_min = wall_y - wall_size_y / 2
wall_y_max = wall_y + wall_size_y / 2

# 最大試行回数（120秒以内に終了）
max_steps = 1000
for step in range(max_steps):
    # 現在の位置を取得
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 赤い箱までの距離
    dx = target_x - x
    dy = target_y - y
    distance_to_target = math.sqrt(dx*dx + dy*dy)
    
    # 距離が非常に近い場合（0.3m未満）は、ゆっくり近づく
    if distance_to_target < 0.3:
        vx = 0.3
        vy = 0.0
    else:
        # 目標点への単位ベクトルで速度を設定（前後方向に進む）
        target_dir_x = dx / distance_to_target
        target_dir_y = dy / distance_to_target
        vx = 0.5 * target_dir_x
        vy = 0.5 * target_dir_y
    
    # 壁との y 方向の安全距離を常に確保（ロボットの中心が壁の y 範囲内に入らないように）
    # 壁の y 範囲: [wall_y_min, wall_y_max]
    # ロボットの中心がこの範囲内に入ると、ぶつかる可能性がある
    if (y < wall_y_min + safe_margin_y) or (y > wall_y_max - safe_margin_y):
        # 壁に近づいている → y 方向にずらす（壁に平行に進む）
        # 壁の中心 y に近づくように、y 方向に移動
        if y < wall_y:
            vy = 0.3
        else:
            vy = -0.3
        # 前後速度を 0 にする（y 方向のみ）
        vx = 0.0
    
    # 速度を範囲内に収める
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # 旋回は不要 → 0
    yaw_rate = 0.0
    
    # 0.1秒間移動（小さなステップで安全に進む）
    walk(vx, vy, yaw_rate, duration=0.1)
    
    # 10ステップごとに位置を確認（進んでいるか確認）
    if step % 10 == 0:
        current_x, current_y = get_position()
        print(f"ステップ {step}: 位置 ({current_x:.2f}, {current_y:.2f}), 向き {current_yaw:.1f} deg")
    
    # 動きが止まっているか確認（10ステップ以上動いていない場合、強制的に進む）
    # ただし、安全距離を満たすまで動くようにする
    if step > 50 and abs(vx) < 0.01 and abs(vy) < 0.01:
        # 動きが止まっている → 10ステップで一度だけ、安全な方向に進むように強制
        if (y < wall_y_min + safe_margin_y) or (y > wall_y_max - safe_margin_y):
            vy = 0.3 if y < wall_y else -0.3
            vx = 0.0
        else:
            # 安全な方向に進む
            target_dir_x = dx / distance_to_target
            vx = 0.3 * target_dir_x
            vy = 0.3 * target_dir_y
        walk(vx, vy, 0.0, duration=0.1)

# ゴールに到達したら、1秒間止まる
stop(1.0)
```