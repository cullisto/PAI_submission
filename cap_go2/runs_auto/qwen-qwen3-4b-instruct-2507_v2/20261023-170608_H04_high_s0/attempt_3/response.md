```python
# 赤い箱の位置を取得
red_box_x, red_box_y = get_object_position("red_box")

# ロボットの現在位置を取得
current_x, current_y = get_position()

# 赤い箱までの距離を計算
distance_to_box = math.hypot(red_box_x - current_x, red_box_y - current_y)

# 障害物の情報を取得（特に奥の壁 wall_back が x=3.0 で、y=0 に存在）
wall_back_x, wall_back_y = get_object_position("wall_back")

# ロボットの前後長さは 0.7m → 前後方向に 0.35m だけ近づくことが安全
# 左右幅は 0.3m → 左右方向に 0.15m だけ近づくことが安全

# よって、安全な経路は：
# 1. 初期位置 (0.0, 0.0) から、x軸方向に進み、x=3.0 まで進む（壁_back に近づくが、ロボットの中心が x=3.0 に近づくと、前端が壁にぶつかる）
# → 安全な距離は、x=3.0 - 0.35 = 2.65 までに進む

# 2. その後、x軸方向に進み、赤い箱 (4.2, 0.0) まで進む

# まず、x=2.65 まで前進（安全に壁に近づかない）
move_forward(2.65)

# 残り距離を計算（赤い箱までの距離）
remaining_x = red_box_x - (current_x + 2.65)
if remaining_x < 0:
    remaining_x = 0

# 残り距離を前進で進む（y方向は0）
move_forward(remaining_x)

# 到達確認（安全距離で）
print("赤い箱へ到達しました")
stop(1.0)
```