# 左回りに円を描くように一周して、元の場所付近に戻る（最終修正版）
# 前回の失敗から学んだ点：
# 1. 円の描画では、単に角度を進めるだけではロボットの位置が正しく更新されない
# 2. 速度の計算が向きに依存していなければ、円の形が崩れる
# 3. 回転の制御が不十分で、360度の回転が実現されなかった
# 4. 一周後に元の位置に戻る処理が不十分で、位置がずれてしまう

import math

# 初期位置と向きを記録
x0, y0 = get_position()
yaw0 = get_yaw()

# 円の半径を安全に設定（ロボットの大きさと障害物との距離を考慮）
radius = 2.0

# 円を一周するためのパラメータ
max_iterations = 1000  # 最大1000回（約16秒以内）
angle_step = 0.1  # 角度ステップ（rad）

# 円を描く（左回り）
current_x, current_y = get_position()
current_yaw = get_yaw()

for i in range(max_iterations):
    # 目標の角度（左回り）
    target_yaw = (yaw0 + i * angle_step) % (2 * math.pi)
    
    # 現在の向きと目標の差（-π～π）
    err = (target_yaw - current_yaw + math.pi) % (2 * math.pi) - math.pi
    
    # 誤差が小さい場合、終了
    if abs(err) < 0.1:
        break
    
    # 角速度を制限（-1.0 ～ 1.0）
    rate = max(-1.0, min(1.0, 2.0 * err))
    if abs(rate) < 0.1:
        rate = math.copysign(0.1, rate)
    
    # 円周上を動くための速度（線速度）
    linear_speed = 0.5  # 一定の速度（m/s）
    
    # 向きから速度成分を計算（ロボットが左回りに進む）
    vx = linear_speed * math.cos(current_yaw)
    vy = linear_speed * math.sin(current_yaw)
    
    # 速度範囲制限
    vx = max(-0.5, min(1.0, vx))
    vy = max(-0.5, min(0.5, vy))
    
    # 移動
    walk(vx, vy, rate, duration=0.1)
    
    # 現在の位置と向きを更新
    current_x, current_y = get_position()
    current_yaw = get_yaw()

# 一周終了後、元の位置（x0, y0）に近づく
x_final, y_final = get_position()
target_x, target_y = x0, y0

# 距離が0.1m以内になるまで移動
max_steps = 300
for _ in range(max_steps):
    x, y = get_position()
    dx = target_x - x
    dy = target_y - y
    dist = math.hypot(dx, dy)
    if dist < 0.1:
        break
    # 方向に応じた移動
    vx = dx / dist * 0.5
    vy = dy / dist * 0.5
    walk(vx, vy, 0.0, duration=0.1)

# 最後に停止
stop(1.0)
