# すべての箱の位置を取得して、ロボットの現在位置から最も近い箱を選び、その場所まで移動する
objects = get_objects()
robot_x, robot_y = get_position()

# 各箱までの距離を計算し、最も近い箱の情報を保存
min_distance = float('inf')
closest_object = None

for obj in objects:
    obj_x, obj_y = obj["x"], obj["y"]
    dist = math.hypot(obj_x - robot_x, obj_y - robot_y)
    if dist < min_distance:
        min_distance = dist
        closest_object = obj

# 最も近い箱の位置に移動するが、到達までに途中で障害物にぶつからないように、
# まず向きを調整し、安全な距離で近づくようにする（直接 move_to ではなく、段階的に移動）

if closest_object:
    target_x, target_y = closest_object["x"], closest_object["y"]
    
    # ロボットの現在の向きを確認し、目標地点に向かって旋回してから移動
    current_yaw = get_yaw()
    target_yaw = math.degrees(math.atan2(target_y - robot_y, target_x - robot_x))
    
    # 旋回を調整（-180〜180度の範囲で計算）
    target_yaw = target_yaw % 360
    if target_yaw > 180:
        target_yaw -= 360
    
    # 目標方向まで旋回（10度ずつ、最大3回まで）
    turn_angle = target_yaw - current_yaw
    # 180度を超える場合は補正（短い回転で調整）
    if abs(turn_angle) > 180:
        turn_angle = turn_angle - 360 if turn_angle > 0 else turn_angle + 360
    
    # 旋回の幅を小さくして、安定した向きに合わせる（10度ずつ）
    turn_steps = 0
    while abs(turn_angle) > 10 and turn_steps < 3:
        turn(10)
        turn_angle = target_yaw - get_yaw()
        turn_steps += 1
    
    # 旋回後に、目標地点まで安全に近づく（距離が0.5m以上なら段階的に移動）
    distance = math.hypot(target_x - robot_x, target_y - robot_y)
    if distance > 0.5:
        # 1mごとに前進（安全な速度で）
        while distance > 0.3:
            move_forward(0.3)
            robot_x, robot_y = get_position()
            distance = math.hypot(target_x - robot_x, target_y - robot_y)
    else:
        # 0.3m以内なら、直進で到達
        move_forward(distance * 0.8)
    
    # 到達確認
    final_distance = math.hypot(target_x - robot_x, target_y - robot_y)
    if final_distance < 0.3:
        print("到着: True")
    else:
        print("到着: False")
else:
    print("物体が見つかりません。")

stop(0.5)
