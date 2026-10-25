"""結果の CSV を集計して、成功率と失敗の内訳の表（Markdown）を作る.

使い方:
    python cap_summary.py                                             # claude.ai（手動）の結果（今のプロンプトの版）
    python cap_summary.py results_qwen-qwen3-4b-instruct-2507_v2.csv  # cap_auto.py の結果
    python cap_summary.py results_v1.csv results_v2.csv               # 版の違うプロンプトの結果を並べて比較
出力: 画面と report_assets/summary_<CSV の名前>.md

1 エピソード = 1 つの実行記録（run_id）。「1 回目で成功」は試行 1 で成功、「修正込み」はいずれかの試行で成功。
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from cap_common import RESULTS_CSV
from tasks import TASKS

CAP_DIR = Path(__file__).resolve().parent
ROOT = CAP_DIR.parent


def prompt_version_of(path):
    """結果の CSV の名前からプロンプトの版を読む（results_v2.csv → v2。版の付かない古い名前は v1）."""
    match = re.search(r"_(v\d+)$", Path(path).stem)
    return match.group(1) if match else "v1"


def load_episodes(paths):
    episodes = defaultdict(list)
    for path in paths:
        version = prompt_version_of(path)
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row["success"] == "":
                    continue  # 未判定（自由な指示）は集計しない
                # 版の違うプロンプトの結果を並べて比べられるよう、モデル名に版を付ける
                episodes[(f"{row['model']} [{version}]", row["api_level"], row["run_id"])].append(row)
    for rows in episodes.values():
        rows.sort(key=lambda r: int(r["attempt"]))
    return episodes


def pct(n, d):
    return f"{n}/{d}（{100 * n / d:.0f}%）" if d else "-"


def summarize(paths):
    episodes = load_episodes(paths)
    groups = defaultdict(list)
    for (model, level, _), rows in episodes.items():
        groups[(model, level)].append(rows)

    lines = [f"# Code as Policies 評価の集計", "", f"入力: {', '.join(Path(p).name for p in paths)}", ""]

    # 1. 全体の成功率
    lines += ["## 全体の成功率", "", "| モデル | API レベル | エピソード数 | 1 回目で成功 | 修正込みで成功 | 成功までの平均試行回数 |",
              "|---|---|---|---|---|---|"]
    for (model, level), eps in sorted(groups.items()):
        first = sum(rows[0]["success"] == "1" for rows in eps)
        final = [rows for rows in eps if any(r["success"] == "1" for r in rows)]
        # 記録に残っている試行の数で数える（操作ミスなどで無効にした試行の行は results から削除されている）
        mean_attempts = sum(next(i for i, r in enumerate(rows, 1) if r["success"] == "1") for rows in final) / len(final) if final else 0
        lines.append(f"| {model} | {level} | {len(eps)} | {pct(first, len(eps))} | {pct(len(final), len(eps))} | "
                     f"{mean_attempts:.2f} |")

    # 2. タスクごとの成功率（1 回目 / 修正込み）
    columns = sorted(groups)
    lines += ["", "## タスクごとの成功数（1 回目 / 修正込み / エピソード数）", "",
              "| タスク | 種類 | " + " | ".join(f"{m} [{lv}]" for m, lv in columns) + " |",
              "|---|---|" + "---|" * len(columns)]
    task_ids = sorted({rows[0]["task_id"] for eps in groups.values() for rows in eps},
                      key=lambda t: (t[0] != "T", t))
    for task_id in task_ids:
        cells = []
        for key in columns:
            eps = [rows for rows in groups[key] if rows[0]["task_id"] == task_id]
            if not eps:
                cells.append("-")
                continue
            first = sum(rows[0]["success"] == "1" for rows in eps)
            final = sum(any(r["success"] == "1" for r in rows) for rows in eps)
            cells.append(f"{first} / {final} / {len(eps)}")
        category = TASKS[task_id].category if task_id in TASKS else ""
        lines.append(f"| {task_id} | {category} | " + " | ".join(cells) + " |")

    # 3. 失敗の内訳（すべての失敗した試行）
    lines += ["", "## 失敗の種類（失敗した試行の数）", "",
              "| モデル | API レベル | " + " | ".join(["失敗した試行"]) + " | 内訳 |", "|---|---|---|---|"]
    for (model, level), eps in sorted(groups.items()):
        failures = Counter(r["failure_type"] for rows in eps for r in rows if r["success"] == "0")
        breakdown = "、".join(f"{k} {v}" for k, v in failures.most_common()) or "なし"
        lines.append(f"| {model} | {level} | {sum(failures.values())} | {breakdown} |")

    # 4. 最後まで失敗したエピソード（失敗分析の候補）
    lines += ["", "## 最後まで失敗したエピソード", "", "| モデル | API レベル | タスク | 実行記録 | 各試行の失敗の種類 |",
              "|---|---|---|---|---|"]
    for (model, level), eps in sorted(groups.items()):
        for rows in eps:
            if not any(r["success"] == "1" for r in rows):
                kinds = " → ".join(r["failure_type"] for r in rows)
                lines.append(f"| {model} | {level} | {rows[0]['task_id']} | {rows[0]['run_id']} | {kinds} |")
    return "\n".join(lines) + "\n"


def main():
    paths = sys.argv[1:] or [str(RESULTS_CSV)]
    paths = [p if Path(p).exists() else str(CAP_DIR / p) for p in paths]
    text = summarize(paths)
    print(text)
    out_dir = ROOT / "report_assets"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"summary_{'_'.join(Path(p).stem for p in paths)}.md"
    out_path.write_text(text, encoding="utf-8")
    print(f"保存: {out_path}")


if __name__ == "__main__":
    main()
