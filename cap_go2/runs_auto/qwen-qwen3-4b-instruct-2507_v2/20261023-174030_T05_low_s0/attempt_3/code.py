# 1辺1メートルの正方形を描くように歩くが、正確な軌跡と安全な距離を確保
# 始点(0,0)から(1,0)→(1,1)→(0,1)→(0,0)まで正確に移動し、物体にぶつからないように安全距離を維持
# 各移動は、目標方向に正確に進み、物体との距離を常に確認

import math

# 初期位置と向きを取得
x, y = get_position()
yaw = get_yaw()

# 物体の情報を取得（中心座標と大きさ）
objects = get_objects()
object_positions = {}
for obj in objects:
    object_positions[obj["name"]] = (obj["x"], obj["y"], obj["size_x"], obj["size_y"])

# 1mの正方形の4つの頂点（開始点(0,0)から）
vertices = [
    (1.0, 0.0),   # 右
    (1.0, 1.0),   # 前
    (0.0, 1.0),   # 左
    (0.0, 0.0)    # 後（元の位置に戻る）
]

# 各辺の目標方向（0度：右、90度：前、180度：左、270度：後）
target_yaws = [0.0, 90.0, 180.0, 270.0]

# 安全距離（ロボットの大きさを考慮）
SAFE_DISTANCE_X = 0.35  # 前後方向（胴体長0.7mの半分）
SAFE_DISTANCE_Y = 0.15  # 左右方向（幅0.3mの半分）

# 各移動を正確に、安全に実行（最大100ステップで制御）
for i in range(4):
    target_x, target_y = vertices[i]
    target_yaw = target_yaws[i]
    
    # 1. 目標方向に旋回（90度ずつ）
    current_yaw = get_yaw()
    target_yaw_rad = math.radians(target_yaw)
    current_yaw_rad = math.radians(current_yaw)
    
    # 旋回の誤差（-π〜π）
    angle_diff = (target_yaw_rad - current_yaw_rad) % (2 * math.pi)
    if angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    
    # 旋回速度（最大1.0 rad/s）
    if abs(angle_diff) < 0.1:
        yaw_rate = 0.0
    else:
        yaw_rate = max(-1.0, min(1.0, 1.0 * angle_diff / 0.5))
    
    # 旋回を実行（最大100回、100msごと）
    for _ in range(100):
        current_yaw = get_yaw()
        current_yaw_rad = math.radians(current_yaw)
        angle_diff = (target_yaw_rad - current_yaw_rad) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        if abs(angle_diff) < 0.1:
            break
        walk(0.0, 0.0, yaw_rate, duration=0.1)
    
    # 2. 目標位置まで移動（安全距離を常に確認）
    for step in range(100):
        x, y = get_position()
        current_yaw = get_yaw()
        current_yaw_rad = math.radians(current_yaw)
        
        # 前後の移動ベクトル（目標方向に合わせて）
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        
        # 進む前に、すべての物体との距離をチェック（ぶつからないか）
        safe = True
        for obj_x, obj_y, size_x, size_y in object_positions.values():
            # ロボットの境界（中心から±安全距離）
            robot_left = x - 0.15
            robot_right = x + 0.15
            robot_front = y - 0.35
            robot_back = y + 0.35
            
            # 物体の境界
            obj_left = obj_x - size_x / 2
            obj_right = obj_x + size_x / 2
            obj_front = obj_y - size_y / 2
            obj_back = obj_y + size_y / 2
            
            # 交差チェック（ぶつかる場合）
            if (robot_left < obj_left or robot_right > obj_right or
                robot_front < obj_front or robot_back > obj_back):
                safe = False
                break
        
        # 安全でない場合、移動を中断
        if not safe:
            break
            
        # 進む距離を0.5m/sで制御（1mは2秒で達成）
        if distance < 0.01:
            break
            
        # 前後方向に移動（目標方向に合わせて）
        move_x = math.cos(current_yaw_rad) * 0.5
        move_y = math.sin(current_yaw_rad) * 0.5
        walk(move_x, move_y, 0.0, duration=0.1)
    
    # 位置を更新
    x, y = get_position()

# 最後に元の位置（0,0）に戻る
for step in range(100):
    x, y = get_position()
    dist = math.hypot(x, y)
    if dist < 0.01:
        break
    walk(0.5, 0.0, 0.0, duration=0.1)

# 最終的に止まる
stop(1.0)
