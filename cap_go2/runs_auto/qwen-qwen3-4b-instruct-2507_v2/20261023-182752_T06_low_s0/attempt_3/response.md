```python
# 一番近い箱まで行って、物体にぶつからないように安全な距離で移動する
# 前2回の失敗から、旋回の精度や移動のスピードが足りず、物体に近づいてしまうことが判明
# 修正点:
# 1. 旋回と移動を明確に分離し、常に目標方向に向けながら、安全距離を確保
# 2. 移動速度を小さくし、ステップごとに位置と物体の距離を確認
# 3. 物体に近づくと即座に停止し、安全な距離を保つ
# 4. 向きを正確に調整し、目標の箱に近づくまで繰り返す

import math

# 物体の情報を取得
objects = get_objects()
# 初期状態
x0, y0 = get_position()
current_yaw = get_yaw()

# 各物体の中心と安全距離（ロボットの前後幅0.35mを考慮）
safe_distance = 0.35  # 前後方向の安全距離（物体に当たらないように）

# 最も近い物体を選び、その中心を目標に
min_dist = float('inf')
target_x, target_y = 0.0, 0.0

for obj in objects:
    obj_x, obj_y = obj["x"], obj["y"]
    dist = math.sqrt((obj_x - x0)**2 + (obj_y - y0)**2)
    if dist < min_dist:
        min_dist = dist
        target_x, target_y = obj_x, obj_y

# 安全な目標が見つからなかった場合
if min_dist == float('inf'):
    stop(1.0)
else:
    # 目標方向へのベクトルを計算
    dx = target_x - x0
    dy = target_y - y0
    target_yaw = math.degrees(math.atan2(dy, dx))
    
    # 向きの誤差を計算（-180〜180度）
    yaw_diff = target_yaw - current_yaw
    while yaw_diff > 180:
        yaw_diff -= 360
    while yaw_diff < -180:
        yaw_diff += 360
    
    # 移動ステップ（最大100ステップで制限、1ステップ=0.1秒）
    max_steps = 100
    for step in range(max_steps):
        # 現在の位置を取得
        x, y = get_position()
        
        # ターゲットまでの距離
        current_dist = math.sqrt((x - target_x)**2 + (y - target_y)**2)
        
        # 0.1m以内に達したら終了
        if current_dist < 0.1:
            break
            
        # 向きの誤差が大きい場合、旋回
        if abs(yaw_diff) > 5.0:
            # 旋回速度を小さく（安定性を確保）
            rate = max(-1.0, min(1.0, 2.0 * math.radians(yaw_diff)))
            if abs(rate) < 0.1:
                rate = math.copysign(0.1, rate)
            walk(0.0, 0.0, rate, duration=0.1)
            current_yaw = get_yaw()
            yaw_diff = target_yaw - current_yaw
            while yaw_diff > 180:
                yaw_diff -= 360
            while yaw_diff < -180:
                yaw_diff += 360
        else:
            # 向きが合っている場合、前進（速度を小さく）
            walk(0.2, 0.0, 0.0, duration=0.1)
        
        # 物体に近づいていないか確認（すべての物体に対して）
        # ロボットの中心が物体の境界内に入らないようにチェック
        for obj in objects:
            obj_x, obj_y = obj["x"], obj["y"]
            obj_size_x, obj_size_y = obj["size_x"], obj["size_y"]
            
            # ロボットの中心から物体の中心までの距離
            dx = obj_x - x
            dy = obj_y - y
            dist_to_obj = math.sqrt(dx*dx + dy*dy)
            
            # 前後方向（x軸）での安全距離：0.35m（ロボットの前後幅）
            # 左右方向（y軸）での安全距離：0.15m
            # つまり、物体の中心からロボットの中心までの距離が、0.35m未満なら前後方向にぶつかる
            # 0.15m未満なら左右方向にぶつかる
            if dist_to_obj < 0.35:
                # 前後方向に近づいている → 停止
                print(f"停止: 物体 {obj['name']} に近づいてしまいました")
                stop(1.0)
                break
        else:
            # すべての物体に近づいていない → 繰り返し
            continue
        break  # 物体に近づいた場合、ループを抜ける
    
    # 到達後、1秒間停止
    stop(1.0)
```