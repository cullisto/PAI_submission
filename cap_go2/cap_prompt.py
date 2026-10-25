"""① 自然言語の指示から LLM に渡すプロンプトを作る.

使い方:
    python cap_prompt.py --task T03                 # 評価用タスク（tasks.py）を使う
    python cap_prompt.py "青い箱の周りを一周して"      # 自由な指示（--scene でシーンを選ぶ）
    python cap_prompt.py --list                     # タスク一覧
    python cap_prompt.py --next --api-level low     # 結果の CSV にまだ記録がない次のタスク（T01 → … → H07 の順）

作ったプロンプトは runs/<日時>_<タスク>/attempt_1/prompt.md に保存され、クリップボードにもコピーされる。
claude.ai の「新しいチャット」に貼り付けて、返ってきた応答全体をコピーしてから cap_run.py を実行する。
"""

import argparse
import csv

from cap_common import PROMPT_VERSION, RESULTS_CSV, build_prompt, copy_to_clipboard, new_run_dir, save_json
from robot_api import API_LEVELS
from scenes import SCENES
from tasks import TASKS


def next_task(api_level):
    """結果の CSV にまだ記録がない最初のタスクと、記録済みのタスク数を返す（全部済んでいれば None）."""
    recorded = set()
    if RESULTS_CSV.exists():
        with open(RESULTS_CSV, newline="", encoding="utf-8-sig") as f:
            recorded = {row["task_id"] for row in csv.DictReader(f) if row["api_level"] == api_level}
    remaining = [t for t in TASKS if t not in recorded]
    return (remaining[0] if remaining else None), len(TASKS) - len(remaining)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("instruction", nargs="?", help="自由な指示（--task を使わない場合）")
    parser.add_argument("--task", choices=sorted(TASKS), help="評価用タスクの ID")
    parser.add_argument("--next", action="store_true", help=f"{RESULTS_CSV.name} にまだ記録がない次のタスクを選ぶ")
    parser.add_argument("--scene", choices=sorted(SCENES), default="basic", help="自由な指示のときのシーン")
    parser.add_argument("--api-level", choices=sorted(API_LEVELS), default="high", help="LLM に渡す API の粒度")
    parser.add_argument("--model", default="claude.ai (manual)", help="コード生成に使うモデル名（記録用）")
    parser.add_argument("--list", action="store_true", help="タスク一覧を表示して終了")
    args = parser.parse_args()

    if args.list:
        for t in TASKS.values():
            print(f"{t.task_id}  [{t.scene:8s}] [{t.category}] {t.instruction}")
        return
    if args.next:
        args.task, n_done = next_task(args.api_level)
        if args.task is None:
            print(f"{args.api_level} の {len(TASKS)} タスクはすべて {RESULTS_CSV.name} に記録済みです。")
            return
        print(f"進捗: {args.api_level} は {n_done}/{len(TASKS)} タスク記録済み → 次は {args.task}")
    if (args.task is None) == (args.instruction is None):
        parser.error("--task（または --next）か指示文のどちらか一方を指定してください")

    if args.task is not None:
        task = TASKS[args.task]
        instruction, scene_name, label = task.instruction, task.scene, task.task_id
    else:
        instruction, scene_name, label = args.instruction, args.scene, "free"

    run_dir = new_run_dir(label)
    prompt = build_prompt(SCENES[scene_name], instruction, args.api_level)
    prompt_path = run_dir / "attempt_1" / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    save_json(run_dir / "meta.json", {
        "run_id": run_dir.name,
        "task_id": args.task,
        "instruction": instruction,
        "scene": scene_name,
        "api_level": args.api_level,
        "model": args.model,
        "prompt_version": PROMPT_VERSION,
    })

    print(f"指示      : {instruction}")
    print(f"シーン    : {scene_name} / API レベル: {args.api_level} / プロンプト: {PROMPT_VERSION}")
    print(f"プロンプト: {prompt_path}")
    if copy_to_clipboard(prompt_path):
        print("→ クリップボードにコピーしました。claude.ai の新しいチャットに貼り付けてください。")
    else:
        print("→ 上のファイルを開いて、中身を claude.ai の新しいチャットに貼り付けてください。")
    print("→ 応答全体をコピーしたら: python cap_run.py")


if __name__ == "__main__":
    main()
