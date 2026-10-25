# 2枚の壁の隙間を通り抜けて赤い箱まで行くための最終修正版
# 前回の失敗要因:
# - 壁に近づく判断が遅れて、安全距離を確保できずぶつかった
# - 動作のステップが長く、動かなかった時間が長くなる
# - y方向の移動が不安定で、壁の上下に近づくリスクあり

# 修正点:
# 1. 動作のステップを極めて短く（duration=0.05秒）にし、頻繁に状態を確認
# 2. 毎回の移動前に、壁との距離をリアルタイムでチェック
# 3. 壁に近づいた場合、即座に左右に回避（y方向に0.2mずらす）
# 4. 壁の間を通過する前に、x=2.0に達するまで確実に進む
# 5. 赤い箱に近づくまで、常に安全な距離を保つ

import math

# 初期状態
x, y = get_position()
yaw = get_yaw()

# 赤い箱の位置
target_x, target_y = 4.0, -1.0

# 壁の位置
wall_upper_x, wall_upper_y = 2.0, 2.725
wall_lower_x, wall_lower_y = 2.0, -1.475

# 安全距離（ロボットの幅：前後0.35m、左右0.15m → 壁との距離は0.35m以上）
safe_distance = 0.35

# ステップ1: x軸方向（+x）に向かって向きを調整（0 deg）
for _ in range(300):
    current_yaw = get_yaw()
    err = (0.0 - current_yaw + 180.0) % 360.0 - 180.0
    if abs(err) < 3.0:
        break
    rate = max(-1.0, min(1.0, 2.0 * math.radians(err)))
    if abs(rate) < 0.3:
        rate = math.copysign(0.3, rate)
    walk(0.0, 0.0, rate, duration=0.05)

# ステップ2: 壁の間（x=2.0）に進む（y方向は0に近づく）
for step in range(300):
    x, y = get_position()
    # 壁に近づいていないか確認
    wall_upper_dist = math.sqrt((x - wall_upper_x)**2 + (y - wall_upper_y)**2)
    wall_lower_dist = math.sqrt((x - wall_lower_x)**2 + (y - wall_lower_y)**2)
    
    # 壁に近づいているか？
    if wall_upper_dist < safe_distance or wall_lower_dist < safe_distance:
        # 即座にy方向にずらす（壁に近づかないように）
        walk(0.0, 0.2 if y < wall_lower_y else -0.2, 0.0, duration=0.05)
        continue
    
    # x方向に進む（目標はx=2.0）
    dx = 2.0 - x
    if abs(dx) < 0.1:
        break
    
    # 前進速度を制限（安全に進む）
    vx = min(0.8, 0.5 * dx / abs(dx))
    vy = 0.0
    walk(vx, vy, 0.0, duration=0.05)

# ステップ3: 壁の向こう側（x > 2.0）から赤い箱まで前進
for step in range(300):
    x, y = get_position()
    dx = target_x - x
    dy = target_y - y
    dist = math.sqrt(dx**2 + dy**2)
    
    # 距離が0.5m以上なら前進、それ以下なら停止
    if dist > 0.5:
        vx = min(1.0, 0.6 * dx / dist)
        vy = min(0.3, 0.2 * dy / dist)
        walk(vx, vy, 0.0, duration=0.05)
    else:
        break

# 最後に停止
stop(1.0)
