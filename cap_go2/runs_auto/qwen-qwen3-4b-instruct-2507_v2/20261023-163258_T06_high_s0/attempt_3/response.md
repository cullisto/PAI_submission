```python
# 最も近い箱まで安全に到達するように、物体の大きさとロボットのサイズを考慮して目標位置を調整
# 修正点: 前回は「安全距離」を考慮して移動先をずらしたが、最終的に到達距離が 0.76m（基準 0.7m 未満）だった
# → つまり、目標が「箱に近すぎる」ため、ロボットが物体に当たるリスクがある
# → 修正: 箱までの距離が 0.7m 以下なら、その箱を避けて、次に近い箱をターゲットにする
# → また、安全距離を厳密に確保し、到達距離を 0.7m 以下に抑えるように調整

objects = get_objects()
current_x, current_y = get_position()

# 各箱までの距離を計算し、最も近い箱を決定（安全距離を考慮して）
min_distance = float('inf')
closest_object = None

for obj in objects:
    obj_x, obj_y = obj['x'], obj['y']
    size_x, size_y = obj['size_x'], obj['size_y']
    
    # ロボットの胴体の前後幅 0.35m、左右幅 0.15m → 重心が物体表面に近づかないように安全距離を確保
    # 安全距離：物体の半径 + ロボットの半径（前後方向で 0.35m）
    safe_radius = size_x / 2.0 + size_y / 2.0 + 0.35
    
    dx = obj_x - current_x
    dy = obj_y - current_y
    dist = math.hypot(dx, dy)
    
    # 安全距離より近い場合は、その箱は避ける（到達しない）
    if dist < safe_radius:
        continue
        
    if dist < min_distance:
        min_distance = dist
        closest_object = obj

# 最も安全な箱に移動（距離が 0.7m 以下なら、別の箱を選び直す）
if closest_object:
    target_x, target_y = closest_object['x'], closest_object['y']
    size_x, size_y = closest_object['size_x'], closest_object['size_y']
    
    # 安全距離を確保（物体の半径 + ロボットの半径）
    safe_radius = size_x / 2.0 + size_y / 2.0 + 0.35
    
    dx = target_x - current_x
    dy = target_y - current_y
    dist = math.hypot(dx, dy)
    
    # もし距離が安全距離より近い（安全に近づけない）なら、避ける
    if dist < safe_radius:
        print("安全な距離を確保できず、目標を変更します。")
        # 次に近い箱を探索（安全距離を満たすもの）
        # すべての箱を再検討
        safe_objects = []
        for obj in objects:
            obj_x, obj_y = obj['x'], obj['y']
            size_x, size_y = obj['size_x'], obj['size_y']
            safe_radius = size_x / 2.0 + size_y / 2.0 + 0.35
            dx = obj_x - current_x
            dy = obj_y - current_y
            dist = math.hypot(dx, dy)
            if dist >= safe_radius:
                safe_objects.append(obj)
        
        if safe_objects:
            # 安全な箱の中で最も近いものを選ぶ
            min_dist = float('inf')
            selected = None
            for obj in safe_objects:
                obj_x, obj_y = obj['x'], obj['y']
                dx = obj_x - current_x
                dy = obj_y - current_y
                dist = math.hypot(dx, dy)
                if dist < min_dist:
                    min_dist = dist
                    selected = obj
            if selected:
                target_x, target_y = selected['x'], selected['y']
                reached = move_to(target_x, target_y, tolerance=0.3)
                print("安全な距離を確保した上で到達:", reached)
            else:
                print("安全な目標が見つかりません。停止します。")
                stop(5.0)
        else:
            print("すべての箱が安全距離内にあり、移動できません。停止します。")
            stop(5.0)
    else:
        # 安全な距離を確保して移動（0.7m 以下なら、目標を調整）
        # 0.7m 未満なら、目標を物体の中心から安全距離を確保した位置にずらす
        target_offset = 0.7  # 基準距離
        if dist <= target_offset:
            # 0.7m 以下なら、物体に近すぎるため、安全距離を確保した位置にずらす
            scale = (target_offset - 0.1) / dist  # 0.1m は余裕
            target_x = target_x - (dx / dist) * scale * 0.1
            target_y = target_y - (dy / dist) * scale * 0.1
        else:
            # 0.7m 以上なら、そのまま
            pass
            
        reached = move_to(target_x, target_y, tolerance=0.3)
        print("到達:", reached)
else:
    print("物体が見つかりません。停止します。")
    stop(5.0)
```