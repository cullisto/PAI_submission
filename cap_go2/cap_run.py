"""③ LLM が生成したコードを Genesis 上の Go2 で実行し、結果を記録する.

使い方:
    python cap_run.py                       # 最新の実行記録に、クリップボードの LLM 応答を使う
    python cap_run.py --response resp.md    # 応答をファイルから読む
    python cap_run.py runs/<run_id>         # 実行記録を指定する
    python cap_run.py --viewer              # ビューアで動きを見ながら実行する

保存されるもの（runs/<run_id>/attempt_<N>/）:
    response.md（LLM の応答そのまま）, code.py, video.mp4, trajectory.csv, trajectory.png, run.log, result.json
失敗した場合は、次の試行用のフィードバック（attempt_<N+1>/prompt.md）を作ってクリップボードにコピーする。
"""

import argparse
import builtins
import math
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from cap_common import (
    CAP_DIR, append_result_row, build_retry_prompt, copy_to_clipboard, extract_code, latest_attempt_dir,
    latest_run_dir, load_json, plot_trajectory, read_clipboard, save_json, save_trajectory_csv,
)
from robot_api import API_LEVELS, Go2Robot, RobotAPI, RobotFallenError, SimTimeLimitError
from scenes import SCENES
from tasks import STALL_LIMIT_S, TASKS, stall_time

MAX_ATTEMPTS = 3  # 1 つの指示に対する最大試行回数（初回 + フィードバックによる修正 2 回）

SAFE_BUILTINS = [
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "isinstance", "len", "list", "max", "min",
    "print", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip", "Exception", "ValueError",
    "RuntimeError", "ZeroDivisionError", "IndexError", "KeyError", "TypeError", "True", "False", "None",
]


def restricted_import(name, *args, **kwargs):
    if name == "math":
        return math
    raise ImportError(f"'{name}' は import できません（使えるのは math のみ）")


def build_namespace(api: RobotAPI, api_level, log):
    def logged_print(*args, **kwargs):
        text = " ".join(str(a) for a in args)
        log(f"print: {text}")

    safe_builtins = {name: getattr(builtins, name) for name in SAFE_BUILTINS if hasattr(builtins, name)}
    safe_builtins["print"] = logged_print
    safe_builtins["__import__"] = restricted_import
    namespace = {"__builtins__": safe_builtins, "math": math}
    for name in API_LEVELS[api_level]:
        namespace[name] = getattr(api, name)
    return namespace


def generated_code_traceback(exc, code):
    """トレースバックのうち、生成コード内の行だけを残す（LLM へのフィードバック用）."""
    code_lines = code.splitlines()
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "<generated>"]
    lines = [f"  生成コードの {f.lineno} 行目: {code_lines[f.lineno - 1].strip()}" for f in frames]
    return "\n".join(lines + [f"{type(exc).__name__}: {exc}"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", nargs="?", help="実行記録のディレクトリ（省略時は最新）")
    parser.add_argument("--response", help="LLM の応答を保存したファイル（省略時はクリップボード）")
    parser.add_argument("--viewer", action="store_true", help="ビューアを表示する")
    parser.add_argument("--no-video", action="store_true", help="動画を録画しない（速く実行できる）")
    parser.add_argument("--exp", default=None, help="使う学習済み方策（src_ext/logs/ 以下の名前）")
    parser.add_argument("--judge", choices=["y", "n"], help="自由な指示の成否を手動で記録する")
    parser.add_argument("--results", default=None, help="結果を追記する CSV（省略時は results_<プロンプトの版>.csv）")
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS, help="1 つの指示に対する最大試行回数")
    parser.add_argument("--no-clipboard", action="store_true", help="修正依頼をクリップボードにコピーしない（自動実行用）")
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    meta = load_json(run_dir / "meta.json")
    attempt_dir = latest_attempt_dir(run_dir)
    attempt = int(attempt_dir.name.split("_")[1])
    if (attempt_dir / "result.json").exists():
        sys.exit(f"{attempt_dir} は実行済みです。新しい指示は cap_prompt.py から始めてください。")

    # LLM の応答を保存し、コードを取り出す
    if args.response:
        response = Path(args.response).read_text(encoding="utf-8")
    else:
        response = read_clipboard()
        if "```" not in response and "get_" not in response and "move" not in response and "walk" not in response:
            sys.exit("クリップボードの中身が LLM の応答に見えません。応答全体をコピーしてから実行してください。")
        # プロンプトをコピーしたまま実行してしまった場合（プロンプトの冒頭が含まれている）は実行しない
        prompt_head = (attempt_dir / "prompt.md").read_text(encoding="utf-8").strip()[:40]
        if prompt_head and prompt_head in response:
            sys.exit("クリップボードの中身がプロンプトのままです。LLM の応答をコピーしてから、もう一度実行してください。")
    (attempt_dir / "response.md").write_text(response, encoding="utf-8")
    code = extract_code(response)
    failure_type, error_text = "", ""
    if code is None:
        # 出力が途中で切れた、説明文だけでコードがない、など
        failure_type = "出力形式エラー"
        error_text = "応答から Python のコードブロック（```python ... ```）を取り出せませんでした"
        code = ""
    (attempt_dir / "code.py").write_text(code, encoding="utf-8")

    print(f"実行記録: {run_dir.name} / 試行 {attempt}")
    print(f"指示    : {meta['instruction']}")
    print("---- 生成コード ----")
    print(code)
    print("--------------------")

    log_lines = []

    def log(text):
        line = f"[t={robot.sim_time:6.2f}s] {text}" if robot is not None else text
        log_lines.append(line)
        print(line)

    robot = None
    scene = SCENES[meta["scene"]]
    video_path = None if args.no_video else attempt_dir / "video.mp4"
    robot = Go2Robot(scene, exp_name=args.exp, show_viewer=args.viewer, video_path=video_path)
    log(f"方策: {robot.exp_name} ({robot.ckpt_path.name}), デバイス: {robot.device}")
    api = RobotAPI(robot)
    namespace = build_namespace(api, meta["api_level"], log)

    robot.code_start_time = robot.sim_time
    robot.current_call = "(code)"
    try:
        if not failure_type:
            exec(compile(code, "<generated>", "exec"), namespace)
    except SyntaxError as exc:
        failure_type, error_text = "構文エラー", f"SyntaxError: {exc.msg}（{exc.lineno} 行目）"
    except RobotFallenError as exc:
        failure_type, error_text = "転倒", str(exc)
    except SimTimeLimitError as exc:
        failure_type, error_text = "時間切れ", str(exc)
    except Exception as exc:  # 生成コードの実行時エラーはすべて LLM へのフィードバックとして扱う
        failure_type, error_text = "実行時エラー", generated_code_traceback(exc, code)
    robot.current_call = "(after code)"
    if failure_type != "転倒":
        # 静止させてから最終状態を評価する。この 1 秒は生成コードの実行時間に数えない
        # （時間の上限まで動いたコードのあと、ここで再び時間切れになってプロセスごと落ちないようにする）
        robot.max_sim_time = math.inf
        try:
            robot.run_command(0.0, 0.0, 0.0, 1.0)
        except RobotFallenError as exc:
            if not failure_type:
                failure_type, error_text = "転倒", str(exc)
    robot.close()
    for line in robot.events:
        log_lines.append(line)
    if error_text:
        log(f"エラー: {error_text}")

    # 成功判定（生成コードの実行開始以降の軌跡で判定）
    traj = [r for r in robot.trajectory if r["t"] >= robot.code_start_time]
    task = TASKS.get(meta["task_id"]) if meta["task_id"] else None
    stalled_s = stall_time(traj)
    if failure_type:
        success, detail = False, error_text.splitlines()[-1]
    elif stalled_s > STALL_LIMIT_S:
        success, failure_type = False, "停滞（物体に押し付け）"
        detail = (f"移動の指令を出しているのにほとんど動けなかった時間が合計 {stalled_s:.1f} 秒あった"
                  f"（基準 {STALL_LIMIT_S:.0f} 秒以下）。箱や壁にぶつかったまま前進し続けた可能性がある")
    elif task is not None:
        success, detail = task.check(traj, scene)
        if not success:
            failure_type = "タスク未達成"
    else:
        judge = args.judge or (input("指示どおりに動きましたか？ [y/n]: ").strip().lower() if sys.stdin.isatty() else "")
        success = {"y": True, "n": False}.get(judge)
        detail = "手動判定" if success is not None else "未判定（結果の CSV を手で埋めてください）"
        if success is False:
            failure_type = "タスク未達成（手動判定）"

    sim_time = robot.sim_time - robot.code_start_time
    final = traj[-1]
    result = {
        "success": success,
        "failure_type": failure_type,
        "detail": detail,
        "error": error_text,
        "final_state": {"x": final["x"], "y": final["y"], "yaw_deg": final["yaw_deg"]},
        "sim_time_s": round(sim_time, 2),
        "stall_time_s": round(stalled_s, 2),
        "policy": f"{robot.exp_name}/{robot.ckpt_path.name}",
        "api_calls": robot.events,
        "log_tail": [line for line in log_lines if "print:" in line][-10:],
    }
    save_json(attempt_dir / "result.json", result)
    (attempt_dir / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    save_trajectory_csv(attempt_dir / "trajectory.csv", robot.trajectory)
    status = {True: "成功", False: "失敗", None: "未判定"}[success]
    plot_trajectory(attempt_dir / "trajectory.png", traj, scene,
                    f"{meta['task_id'] or 'free'} 試行{attempt}: {meta['instruction']}（{status}）")
    append_result_row({
        "timestamp": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        "run_id": run_dir.name,
        "task_id": meta["task_id"] or "free",
        "category": task.category if task else "",
        "scene": meta["scene"],
        "instruction": meta["instruction"],
        "api_level": meta["api_level"],
        "model": meta["model"],
        "attempt": attempt,
        "success": "" if success is None else int(success),
        "failure_type": failure_type,
        "detail": detail,
        "sim_time_s": round(sim_time, 2),
        "code_lines": len([line for line in code.splitlines() if line.strip()]),
        "video": "" if video_path is None else os.path.relpath(video_path, CAP_DIR),
    }, results_csv=args.results)

    print("====================")
    print(f"結果: {status}（{failure_type or 'OK'}）")
    print(f"詳細: {detail}")
    print(f"記録: {attempt_dir}")

    if success is False and attempt < args.max_attempts:
        next_dir = run_dir / f"attempt_{attempt + 1}"
        next_dir.mkdir()
        retry_path = next_dir / "prompt.md"
        retry_path.write_text(build_retry_prompt(code, result), encoding="utf-8")
        print(f"→ 修正依頼のプロンプトを作りました: {retry_path}")
        if not args.no_clipboard:
            copied = copy_to_clipboard(retry_path)
            print("→ クリップボードにコピーしました。" if copied else "→ ファイルの中身をコピーしてください。")
            print("  同じチャットに貼り付け、返ってきた応答全体をコピーしてから、もう一度 python cap_run.py を実行してください。")
    elif success is False:
        print(f"→ 最大試行回数 {args.max_attempts} 回に達しました。")


if __name__ == "__main__":
    main()
