# 自然言語指示による四足歩行ロボットの制御：強化学習の歩行方策と Code as Policies の階層化

PAI2026_応用Ⅰ 最終課題のコード一式。

物理シミュレータ [Genesis](https://github.com/Genesis-Embodied-AI/genesis-world) 上の四足歩行ロボット Unitree Go2 を、自然言語の指示で動かす。
足の動かし方は強化学習（PPO）で獲得した全方向の歩行方策が担い、「どこへ・どう動くか」は大規模言語モデル（LLM）が生成する Python コードが決める（Code as Policies の階層構成）。

デモ動画: https://youtu.be/0xHypHEJgHQ

```
自然言語の指示 ──▶ プロンプト生成 ──▶ LLM ──▶ Python コード（ロボットの API を呼ぶ）
                                                    │
                                                    ▼
   結果の記録 ◀── 自動判定 ◀── Genesis で実行（API → 速度指令 → 歩行方策 → 関節）
   失敗したら、失敗の種類・最終位置・ログを LLM に返してコードを直させる（最大 3 回）
```

## 主な結果

18 個のタスク（前進・旋回・物体への移動・円や正方形の軌跡・一番近い箱・障害物の回避など）で、API の抽象度が高い条件（high: `move_to`・`turn`・`face` など）と低い条件（low: `walk` と位置・向きの取得のみ）を比べた。どの条件のプロンプトにも、ロボットの大きさを書いている。

| LLM | high | low |
|---|---|---|
| claude.ai（Opus 5.5） | 18 / 18（すべて 1 回目） | 18 / 18（すべて 1 回目） |
| Qwen3-4B-Instruct-2507（事後学習なし） | 7 / 18 | 2 / 18 |

- claude.ai は low では `move_to` などに相当する関数をタスクごとに自作し直し、コードが約 1.6 倍に増えた。
- Qwen3-4B の失敗 83 試行のうち 46 試行（55%）は、物体に押し付けたまま前進し続ける「停滞」だった。この停滞は最終位置だけの判定では見逃される（停滞の判定を外すと 10 試行が「成功」になる）ため、実行中の速さも見て判定している。

## フォルダ構成

| パス | 内容 |
|---|---|
| `src_ext/` | 歩行方策の学習・確認（`go2_env.py`、`go2_train.py`、`go2_eval.py`）と学習済みモデル（`logs/go2-omni/model_500.pt` など） |
| `cap_go2/` | Code as Policies の本体。ロボットの API、シーン、タスクと自動判定、プロンプト、実行・記録、自動評価、集計。詳しくは [`cap_go2/README.md`](cap_go2/README.md) |
| `cap_go2/runs/` | claude.ai での全試行の記録（プロンプト、応答、実行したコード、動画、軌跡、判定） |
| `cap_go2/runs_auto/` | Qwen3-4B での全試行の記録（Colab で実行したため動画なし） |
| `cap_go2/results_v2.csv`、`cap_go2/results_qwen-qwen3-4b-instruct-2507_v2.csv` | 全試行の結果の一覧（v2 はロボットの大きさをプロンプトに書いた版。レポートの結果はすべて v2） |
| `report_tools/`、`report_assets/` | 学習曲線の図と、結果の集計表 |
| `movie_build/` | デモ動画の組み立て（Qwen の試行を手元で実行し直して録画する `replay_qwen.py`、動画を組み立てる `make_movie.py`） |
| `movie/` | デモ動画のオープニング・エンディング |

## 環境構築

動作を確認した環境:

| 用途 | 環境 |
|---|---|
| 歩行方策の学習、Qwen3-4B による自動評価 | Google Colab（T4 GPU）、Genesis 1.4.4、rsl_rl v1.0.2 |
| 学習結果の確認、CaP の実行、動画の作成 | Windows 11（GPU なし、CPU で実行）、Python 3.11、Genesis 1.4.4、rsl_rl v1.0.2 |

手元の環境は [uv](https://docs.astral.sh/uv/) で作る。Genesis と rsl_rl は、このリポジトリの直下に置く（`.gitignore` で除外している）。

```powershell
# Genesis（1.4.4 で動作を確認。uv が対応する Python を用意する）
git clone https://github.com/Genesis-Embodied-AI/genesis-world.git
cd genesis-world
uv sync
# PyTorch（GPU がない場合は CPU 版）
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
# rsl_rl v1.0.2（依存関係は入れない。CPU 版の torch が置き換えられるのを防ぐため）
git clone -b v1.0.2 https://github.com/leggedrobotics/rsl_rl.git ../rsl_rl
uv pip install --no-deps -e ../rsl_rl
# CaP の実行・集計・動画の作成に使うもの
uv pip install matplotlib tensorboard moviepy
cd ..
```

以下のコマンドは、この環境の Python で実行する。Windows では、Genesis のログの絵文字でエラーにならないよう `PYTHONUTF8=1` を設定する。

```powershell
$env:PYTHONUTF8 = 1
$py = "genesis-world\.venv\Scripts\python"
```

## 使い方

### 1. 歩行方策の学習（Colab、T4 GPU）

Colab に入っている TensorFlow が Genesis と衝突して segfault するため、新しいランタイムでは最初にアンインストールする。

```python
!pip uninstall -y tensorflow
# Genesis と rsl_rl v1.0.2 をインストールしてから
%cd src_ext
!python go2_train.py -e go2-omni --max_iterations 500
```

前後 -0.5〜1.0 m/s、左右 ±0.5 m/s、旋回 ±1.0 rad/s の速度指令に従い、10% の確率で停止指令も学習する。学習済みのモデルは `src_ext/logs/go2-omni/` に入っている。

### 2. 学習結果の確認（手元）

```powershell
cd src_ext
& "..\$py" go2_eval.py -e go2-omni --ckpt 500
```

### 3. 自然言語で動かす（claude.ai を手動で使う）

```powershell
cd cap_go2
& "..\$py" cap_prompt.py --task T03 --api-level high   # プロンプトを作ってクリップボードにコピー
#   claude.ai の新しいチャットに貼り付け → 応答全体をコピー
& "..\$py" cap_run.py                                  # クリップボードの応答を実行・判定・記録
#   失敗したら修正依頼がクリップボードに入るので、同じチャットに貼り付けて応答をコピー → cap_run.py をもう一度
```

自由な指示も使える（例: `cap_prompt.py "青い箱の周りを一周して" --scene basic`）。オプションと記録の形式は [`cap_go2/README.md`](cap_go2/README.md) を参照。

### 4. オープンウェイトの LLM で自動評価する（Colab、T4 GPU）

```python
!pip uninstall -y tensorflow
!pip install transformers
%cd cap_go2
!python cap_auto.py --backend hf --model Qwen/Qwen3-4B-Instruct-2507 --samples 1
```

生成 → 実行・判定 → 修正依頼を、18 タスク × 2 つの API レベルについて自動でくり返す。途中で止まっても、同じコマンドで続きから再開する。

### 5. 集計

```powershell
cd cap_go2
& "..\$py" cap_summary.py results_v2.csv results_qwen-qwen3-4b-instruct-2507_v2.csv
```

### 6. デモ動画の作成

```powershell
& $py movie_build\replay_qwen.py   # Qwen の試行を、記録した応答から手元で実行し直して録画する
& $py movie_build\make_movie.py    # movie_build\out\ に動画を書き出す
```

## 参考

- J. Liang et al., "Code as Policies: Language Model Programs for Embodied Control," ICRA 2023.
- Genesis: https://github.com/Genesis-Embodied-AI/genesis-world
- rsl_rl: https://github.com/leggedrobotics/rsl_rl
- 歩行学習の手順は次の記事を参考にし、全方向・停止に対応するよう学習設定を変えた。
  - https://tototototototo7.hatenablog.com/entry/2025/genesis_test_google_colab
  - https://note.com/npaka/n/n4ce9e0f69d33
