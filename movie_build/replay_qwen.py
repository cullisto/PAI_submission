"""Colab で録画しなかった Qwen の試行を、記録してある応答から手元で実行し直して録画する.

使い方（last_submission/ から、実験側の環境で）:
    genesis-world/.venv/Scripts/python movie_build/replay_qwen.py

出力: movie_build/replay/<run_id>_attempt<N>/attempt_1/video.mp4 など（cap_run.py と同じ形式）。
実行し直した結果（失敗の種類・最終位置）を、Colab での記録と並べて表示する。
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP_DIR = ROOT / "cap_go2"
RUNS = CAP_DIR / "runs_auto" / "qwen-qwen3-4b-instruct-2507_v2"
OUT = Path(__file__).resolve().parent / "replay"

# 動画に使う試行（実行記録, 試行）
TARGETS = [
    ("20261023-164303_T10_high_s0", 1),
    ("20261023-185446_T10_low_s0", 1),
    ("20261023-162535_T03_high_s0", 1),
    ("20261023-162535_T03_high_s0", 2),
    ("20261023-164025_T09_high_s0", 2),
]


def main():
    for run_id, attempt in TARGETS:
        src = RUNS / run_id
        src_attempt = src / f"attempt_{attempt}"
        dest = OUT / f"{run_id}_attempt{attempt}"
        if (dest / "attempt_1" / "result.json").exists():
            print(f"実行済み: {dest.name}")
        else:
            if dest.exists():
                shutil.rmtree(dest)
            (dest / "attempt_1").mkdir(parents=True)
            shutil.copy(src / "meta.json", dest / "meta.json")
            shutil.copy(src_attempt / "prompt.md", dest / "attempt_1" / "prompt.md")
            cmd = [sys.executable, "cap_run.py", str(dest), "--response", str(src_attempt / "response.md"),
                   "--results", str(dest / "results.csv"), "--max-attempts", "1", "--no-clipboard"]
            with open(dest / "cap_run_output.log", "w", encoding="utf-8") as log:
                subprocess.run(cmd, cwd=CAP_DIR, stdout=log, stderr=subprocess.STDOUT, check=True)
        original = json.loads((src_attempt / "result.json").read_text(encoding="utf-8"))
        replayed = json.loads((dest / "attempt_1" / "result.json").read_text(encoding="utf-8"))
        for name, r in (("Colab", original), ("手元", replayed)):
            f = r["final_state"]
            print(f"{run_id} 試行{attempt} {name}: {r['failure_type'] or '成功'}, 停滞 {r['stall_time_s']} s, "
                  f"時間 {r['sim_time_s']} s, 最終 ({f['x']:.2f}, {f['y']:.2f}, {f['yaw_deg']:.0f}°)", flush=True)


if __name__ == "__main__":
    main()
