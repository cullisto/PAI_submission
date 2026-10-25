# cap_go2: 自然言語で Go2 を動かす（Code as Policies）

自然言語の指示を LLM に渡して、ロボットを動かす Python コードを生成させ、Genesis 上の Go2 で実行する。
歩行そのもの（関節の動かし方）は強化学習で学習した方策が担当し、LLM は「どこへ・どう動くか」をコードで決める。

```
自然言語の指示 ──▶ プロンプト生成 ──▶ LLM（claude.ai, 手動） ──▶ Python コード
                    (cap_prompt.py)                                  │
                                                                     ▼
       結果の記録 ◀── 成功判定 ◀── Genesis で実行（RobotAPI → 速度指令 → RL 歩行方策 → 関節）
                                        (cap_run.py)
       失敗したら エラー・最終状態をフィードバックとして LLM に返し、修正させる（最大 3 回）
```

## 使い方（PowerShell）

```powershell
cd C:\matsuo-ai\PAI-1\last_submission\cap_go2
$env:PYTHONUTF8=1
$py = "..\genesis-world\.venv\Scripts\python"

& $py cap_prompt.py --list          # タスク一覧
& $py cap_prompt.py --task T03      # ① プロンプトを作ってクリップボードにコピー
#   ② claude.ai の「新しいチャット」に貼り付け → 応答全体をコピー（応答の下のコピーボタン）
& $py cap_run.py                    # ③ クリップボードの応答を実行して記録
#   失敗したら、修正依頼がクリップボードに入るので「同じチャット」に貼り付け → 応答をコピー → ③ をもう一度

& $py cap_prompt.py "青い箱の周りを一周して" --scene basic   # 自由な指示
& $py cap_run.py --viewer           # ビューアで見ながら実行
```

主なオプション:
- `cap_prompt.py --api-level low|high`: LLM に渡す API の粒度（low は速度指令と位置取得だけ）
- `cap_prompt.py --model "claude.ai Opus 5.5"`: 記録用のモデル名
- `cap_run.py --exp go2-omni`: 使う学習済み方策（省略時は go2-omni、なければ go2-walking）
- `cap_run.py --no-video`: 録画しない（速い）

## 記録されるもの

- `runs/<日時>_<タスク>/attempt_<N>/`
  - `prompt.md`（LLM に渡したもの）、`response.md`（LLM の応答そのまま）、`code.py`（実行したコード）
  - `video.mp4`（俯瞰カメラの録画）、`trajectory.png`（上から見た軌跡）、`trajectory.csv`
  - `run.log`（API 呼び出しと print の記録）、`result.json`（成否・失敗の種類・最終状態）
- `results_<プロンプトの版>.csv`（例: `results_v2.csv`）: 全試行の一覧（Excel で開ける）。成功率や失敗の種類の集計に使う。
  プロンプトの版は `cap_common.py` の `PROMPT_VERSION`（v1: 最初の版、`prompts/v1/` に保存。v2: ロボットの大きさを追記）

## ファイル構成

| ファイル | 内容 |
|---|---|
| `robot_api.py` | Go2 の実行環境（`Go2Robot`）と LLM に公開する API（`RobotAPI`）。docstring がそのままプロンプトの API 説明になる |
| `scenes.py` | シーン（箱や障害物の配置）: basic / obstacle / gap / maze / danger |
| `tasks.py` | 評価用の指示（基本 T01〜T11、難しいタスク H01〜H07）と自動の成功判定。全タスク共通で「物体に押し付けたままの停滞が 3 秒超」も失敗にする |
| `prompts/` | プロンプトのテンプレートと例（few-shot） |
| `cap_prompt.py` / `cap_run.py` | ① プロンプト生成 / ③ 実行・記録 |
| `cap_common.py` | 共通処理（プロンプト組み立て、記録、クリップボード、軌跡の図） |

## オープンウェイトの LLM で自動評価する（`cap_auto.py`）

LLM の生成 → 実行・判定 → 失敗したら修正依頼を会話に追加して再生成（最大 3 回）を、タスク × API レベル × サンプル数だけ自動でくり返す。
実行・判定は `cap_run.py` を別プロセスで呼ぶ（手動のときと同じ判定）。実行記録は手動の `runs/` と分けて `runs_auto/<モデル名>/` に保存する。

### Colab（T4 GPU）での手順

前提: Drive の `pai1/` に `cap_go2/`（このフォルダ）と最新の `src_ext/go2_env.py`（`scene_setup` 付き）、`src_ext/logs/go2-omni/` がある。

```python
from google.colab import drive
drive.mount('/content/drive')
!pip uninstall -y tensorflow          # Genesis と衝突して segfault するため（毎セッション必要）
# ここで、学習（go2_train.py）のときと同じ手順で Genesis と rsl_rl v1.0.2 をインストールする
%cd /content/drive/MyDrive/matsuo_ai/pai1/cap_go2
!python cap_auto.py --backend hf --model Qwen/Qwen3-4B-Instruct-2507 --samples 1
```

- 途中で切れても、同じコマンドをもう一度実行すれば続きから再開する（`auto_progress_<名前>.jsonl`）。
- `--samples` を後から増やすと、足りない分だけ追加で実行する（例: 1 で一通り回してから 3 に増やす）。
- 一部だけ: `--tasks H01 H04`、`--tasks basic`（T01〜T11）、`--tasks hard`（H01〜H07）、`--api-levels high`
- 思考モード: `--thinking`（`Qwen/Qwen3-4B` のように思考モードを切り替えられるモデル向け。生成が長くなる）
- 動画: 既定では録画しない（Colab では描画できないことがあるため）。気になるエピソードは、`runs_auto/.../response.md` を手元で `cap_prompt.py --task <ID> --api-level <レベル>` → `cap_run.py --response <response.md のパス>` として再実行すると、動画付きで再現できる。

### 手元の OpenAI 互換サーバー（Ollama など）を使う場合

```powershell
& $py cap_auto.py --backend openai --base-url http://localhost:11434/v1 --model <サーバー上のモデル名> --samples 1 --tasks T01
```

### 集計

```powershell
& $py cap_summary.py results_qwen-qwen3-4b-instruct-2507_v2.csv   # 成功率・タスク別・失敗の種類・最後まで失敗した例
& $py cap_summary.py results_v2.csv results_qwen-qwen3-4b-instruct-2507_v2.csv   # claude.ai と並べて比較
```
結果の表は `report_assets/summary_<名前>.md` にも保存される。

## 手動で LLM を使うときの注意（API と同じ条件にするため）

- 指示ごとに claude.ai の「新しいチャット」を使う（修正依頼だけは同じチャット）
- 生成されたプロンプトに手で補足を書き足さない
- コード生成は claude.ai で行う（このプロジェクトのコードを知っている Claude Code には書かせない）
