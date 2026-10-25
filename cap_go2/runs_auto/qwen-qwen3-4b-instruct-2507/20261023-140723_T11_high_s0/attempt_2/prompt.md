前回のコードを実行したところ、指示を達成できませんでした。

## 実行結果
- 失敗の種類: 実行時エラー
- 詳細: NameError: name 'wall_size_x' is not defined
- 実行後のロボットの位置: (-0.01, -0.00)、向き: -0 deg

## エラー
```
生成コードの 16 行目: wall_left = wall_x - wall_size_x / 2
NameError: name 'wall_size_x' is not defined
```

原因を考えて、修正したコード全体を ```python のコードブロック 1 つで出力してください。