# 壁にぶつからないように、安全な経路を確保し、赤い箱まで確実に進む
# 壁: (2.0, 0.0), 大きさ 0.3×1.6 → y方向範囲 [-0.8, 0.8]（中央にy=0.0）
# ロボットは (0.0, 0.0) から出発。壁にぶつからないように、y方向にずらして進む。

# 1. 初期状態で、y方向に0.4mずらして前に進む（壁のy範囲内に留まる）
move_sideways(0.4)

# 2. 壁のx=2.0まで進む（x方向に2.0m）
# ただし、y方向が壁の範囲内に保たれるように、x方向に進む
move_forward(2.0)

# 3. 現在の位置を確認
x, y = get_position()
print(f"壁の前到達: ({x:.2f}, {y:.2f})")

# 4. y方向が壁の範囲（-0.8 〜 0.8）を超えていないかチェック
if y > 0.8 or y < -0.8:
    # 超えていたら、y方向に調整（壁に近づかないように）
    move_sideways(-0.4)  # y方向に0.4m戻す

# 5. 赤い箱 (4.0, 0.0) に向かって進む
# 現在のx座標から4.0までの距離を計算
distance_x = 4.0 - x
move_forward(distance_x)

# 6. 到着確認（赤い箱の中心まで0.3m以内か）
target_x, target_y = 4.0, 0.0
final_x, final_y = get_position()
distance = math.hypot(target_x - final_x, target_y - final_y)
print(f"赤い箱までの距離: {distance:.2f}m")

# 7. 距離が0.3m以上なら、さらに0.5m前進
if distance > 0.3:
    move_forward(0.5)

# 8. 最後に停止（安全に終了）
stop(1.0)
