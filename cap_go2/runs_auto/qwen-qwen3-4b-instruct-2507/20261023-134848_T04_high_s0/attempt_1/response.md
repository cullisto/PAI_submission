```python
# 青い箱の位置を取得して、その近くに寄る
bx, by = get_object_position("blue_box")
# ロボットが現在の位置から青い箱まで移動（障害物は考慮しない）
reached_blue = move_to(bx, by, tolerance=0.3)
print("青い箱に到達:", reached_blue)

# 青い箱に到着したら、緑の箱の位置を取得
if reached_blue:
    gx, gy = get_object_position("green_box")
    # 緑の箱まで移動
    reached_green = move_to(gx, gy, tolerance=0.3)
    print("緑の箱に到達:", reached_green)
    
    # 到達した場合、停止
    if reached_green:
        stop(1.0)
else:
    # 青い箱に到達できなかった場合、10秒後に停止
    stop(10.0)
```