前回のコードを実行したところ、指示を達成できませんでした。

## 実行結果
- 失敗の種類: 実行時エラー
- 詳細: TypeError: RobotAPI.turn_to() takes 2 positional arguments but 3 were given
- 実行後のロボットの位置: (-0.01, -0.00)、向き: -0 deg

## エラー
```
生成コードの 12 行目: turn_to(bx - x, by - y)  # 向きを調整（atan2で方向を計算）
TypeError: RobotAPI.turn_to() takes 2 positional arguments but 3 were given
```

原因を考えて、修正したコード全体を ```python のコードブロック 1 つで出力してください。