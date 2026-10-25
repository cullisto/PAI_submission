前回のコードを実行したところ、指示を達成できませんでした。

## 実行結果
- 失敗の種類: 停滞（物体に押し付け）
- 詳細: 移動の指令を出しているのにほとんど動けなかった時間が合計 22.7 秒あった（基準 3 秒以下）。箱や壁にぶつかったまま前進し続けた可能性がある
- 実行後のロボットの位置: (1.51, 0.01)、向き: -1 deg

## 実行ログ（最後の部分）
```
[t= 11.10s] print: Step 100: pos=1.51,0.03, yaw=-2.6deg, dist_to_target=2.49
[t= 12.10s] print: Step 110: pos=1.51,0.03, yaw=-3.3deg, dist_to_target=2.49
[t= 13.10s] print: Step 120: pos=1.51,0.03, yaw=-2.8deg, dist_to_target=2.49
[t= 14.10s] print: Step 130: pos=1.51,0.03, yaw=-3.7deg, dist_to_target=2.49
[t= 15.10s] print: Step 140: pos=1.51,0.03, yaw=-2.7deg, dist_to_target=2.49
[t= 16.10s] print: Step 150: pos=1.51,0.04, yaw=-3.7deg, dist_to_target=2.49
[t= 17.10s] print: Step 160: pos=1.51,0.04, yaw=-3.9deg, dist_to_target=2.49
[t= 18.10s] print: Step 170: pos=1.51,0.04, yaw=-4.3deg, dist_to_target=2.49
[t= 19.10s] print: Step 180: pos=1.51,0.03, yaw=-2.9deg, dist_to_target=2.49
[t= 20.10s] print: Step 190: pos=1.51,0.04, yaw=-3.8deg, dist_to_target=2.49
```

原因を考えて、修正したコード全体を ```python のコードブロック 1 つで出力してください。