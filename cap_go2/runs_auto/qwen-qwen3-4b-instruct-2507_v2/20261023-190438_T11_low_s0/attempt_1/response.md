```python
# 赤い箱までの道を計画する。まず壁にぶつからないようにして、箱に近づく。
# 壁は (2.0, 0.0) で 0.3m × 1.6m なので、ロボットの中心が壁に近づかないよう、
# 壁の左側（y 方向）に少し離れて進む必要がある。

# 初期位置と向きを取得
x0, y0 = get_position()
yaw0 = get_yaw()

# 目標位置：赤い箱の中心 (4.0, 0.0)
target_x, target_y = 4.0, 0.0

# 壁の中心 (2.0, 0.0) と大きさを取得
wall_x, wall_y = 2.0, 0.0
wall_size_x, wall_size_y = 0.3, 1.6

# ロボットのサイズから、壁に近づけない距離を計算
# ロボットの幅は左右 0.3m、前後 0.7m。左右方向の安全距離は 0.15m。
# 壁の中心からロボットの中心が y 方向に 0.15m より近づかないようにする。
# つまり、y が 0 で、壁の y 方向幅は 1.6m なので、y 方向に動かさない。

# まず、壁にぶつからないように y 方向に動かさず、x 方向に進む。
# ただし、壁の x 方向幅は 0.3m なので、x 方向の安全距離は 0.35m（ロボットの前後幅の半分）。
# つまり、x が 2.0 - 0.35 = 1.65m 以下で安全。x が 2.0 + 0.35 = 2.35m 以上でも安全。

# よって、x が 1.65 から 2.35 の間は壁に近づくと危険。安全な範囲は x < 1.65 または x > 2.35。

# しかし、目標は (4.0, 0.0) なので、x > 2.35 で進むのが最善。
# そのため、まず x 方向に進みつつ、壁にぶつからないようにする。

# 1. 壁に近づかないように、x が 2.35m を超えるまで前進
max_steps = 300
for step in range(max_steps):
    x, y = get_position()
    current_yaw = get_yaw()
    
    # 壁の中心からの距離（x 方向）
    wall_dist_x = abs(x - wall_x)
    # 壁の中心からロボットの中心までの距離（x 方向）
    # 壁の x 方向幅は 0.3m なので、ロボットの中心が x 方向で ±0.15m より外れると安全
    safe_x_dist = 0.35  # 前後方向の安全距離（ロボットの半幅）
    
    # 壁に近づいていないかチェック
    if x < wall_x - safe_x_dist or x > wall_x + safe_x_dist:
        # 安全な位置であれば、目標に向かって進む
        # ターゲットまでの距離を計算
        dist_to_target = math.sqrt((x - target_x)**2 + (y - target_y)**2)
        if dist_to_target < 0.1:  # ほぼ到達
            break
            
        # 目標方向へのベクトル
        dx = target_x - x
        dy = target_y - y
        angle_to_target = math.atan2(dy, dx)
        
        # ロボットの現在の向き（rad）から差分を計算
        current_angle = math.radians(current_yaw)
        angle_diff = angle_to_target - current_angle
        
        # 角度差を 0 に近づけるために、旋回
        # ただし、壁に近づかないように、x 方向の移動を優先
        # よって、x 方向の速度を高く、y 方向は 0 にする
        
        # 前後速度を 0.8 に設定（最大 1.0 まで）
        vx = 0.8
        vy = 0.0
        
        # 旋回は、目標方向に近づくように
        if abs(angle_diff) > 0.1:
            yaw_rate = max(-1.0, min(1.0, 2.0 * angle_diff))
        else:
            yaw_rate = 0.0
            
        # 現在の位置が目標に近い場合は、ゆっくり進む
        if dist_to_target < 0.5:
            vx = 0.3
            
        walk(vx, vy, yaw_rate, duration=0.1)
    else:
        # 壁に近づいている（安全範囲内ではない）→ 停止して、壁の方向を確認
        stop(duration=0.5)
        # 壁の前後に移動（y 方向に動かす）は危険なので、ここでは x 方向を再調整
        # ここで、y 方向に動かさず、x を安全な範囲に保つ
        break

# 最後に、目標位置に近づくまでゆっくり進む
for step in range(300):
    x, y = get_position()
    dist_to_target = math.sqrt((x - target_x)**2 + (y - target_y)**2)
    if dist_to_target < 0.2:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)
    
# 到達後、少し止める
stop(duration=1.0)
```