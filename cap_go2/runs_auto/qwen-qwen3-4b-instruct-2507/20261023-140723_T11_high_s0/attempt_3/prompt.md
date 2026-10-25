前回のコードを実行したところ、指示を達成できませんでした。

## 実行結果
- 失敗の種類: 実行時エラー
- 詳細: IndexError: tuple index out of range
- 実行後のロボットの位置: (-0.01, -0.00)、向き: -0 deg

## エラー
```
生成コードの 10 行目: wall_size_x, wall_size_y = wall_info[2], wall_info[3]  # x方向とy方向の大きさ
IndexError: tuple index out of range
```

原因を考えて、修正したコード全体を ```python のコードブロック 1 つで出力してください。