"""cap_prompt.py / cap_run.py で共通に使う処理（プロンプト生成、実行記録の保存、クリップボード）."""

import csv
import json
import math
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scenes import SceneSpec

# プロンプトの版。v1: 最初の版（prompts/v1/ に保存）。v2: ロボットの大きさ（物体にどこまで近づけるか）を追記した版。
# high の例にだけ「箱の手前 0.5 m で止める」という手がかりがあったため、物理的な情報を両方のレベルに与えた。
# 版ごとに結果の CSV を分け、版の違う結果が混ざらないようにする。
PROMPT_VERSION = "v2"

CAP_DIR = Path(__file__).resolve().parent
PROMPT_DIR = CAP_DIR / "prompts"
RUNS_DIR = CAP_DIR / "runs"
RESULTS_CSV = CAP_DIR / f"results_{PROMPT_VERSION}.csv"
PENDING_CSV = CAP_DIR / f"results_{PROMPT_VERSION}_pending.csv"

RESULTS_FIELDS = [
    "timestamp", "run_id", "task_id", "category", "scene", "instruction", "api_level", "model", "attempt",
    "success", "failure_type", "detail", "sim_time_s", "code_lines", "video",
]


# ---------------- プロンプト ----------------
def fmt(value):
    """座標や大きさを、丸めずに必要な桁だけ表示する（例: 2.0, 2.325）."""
    text = f"{value:.3f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def scene_prompt_parts(scene: SceneSpec):
    rows = ["| name | 説明 | 中心 (x, y) [m] | 大きさ x × y [m] | 障害物 |", "|---|---|---|---|---|"]
    for o in scene.objects:
        rows.append(
            f"| {o.name} | {o.description} | ({fmt(o.pos[0])}, {fmt(o.pos[1])}) | {fmt(o.size[0])} × {fmt(o.size[1])} | "
            f"{'はい' if o.is_obstacle else 'いいえ'} |"
        )
    x0, y0 = scene.robot_start
    state = f"- 位置: ({x0:.1f}, {y0:.1f})\n- 向き: {scene.robot_start_yaw_deg:.0f} deg（静止している）"
    return scene.description, "\n".join(rows), state


def build_prompt(scene: SceneSpec, instruction: str, api_level: str):
    from robot_api import api_reference  # Genesis の読み込みを伴うため、必要になってから import する

    scene_description, objects_table, robot_state = scene_prompt_parts(scene)
    template = (PROMPT_DIR / "template_ja.md").read_text(encoding="utf-8")
    examples = (PROMPT_DIR / f"examples_{api_level}.md").read_text(encoding="utf-8").strip()
    replacements = {
        "scene_description": scene_description,
        "objects_table": objects_table,
        "robot_state": robot_state,
        "api_reference": api_reference(api_level),
        "examples": examples,
        "instruction": instruction,
    }
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def build_retry_prompt(code, result):
    """失敗したときに同じチャットへ貼り付けるフィードバック."""
    lines = ["前回のコードを実行したところ、指示を達成できませんでした。", "", "## 実行結果"]
    lines.append(f"- 失敗の種類: {result['failure_type']}")
    lines.append(f"- 詳細: {result['detail']}")
    fx, fy, fyaw = result["final_state"]["x"], result["final_state"]["y"], result["final_state"]["yaw_deg"]
    lines.append(f"- 実行後のロボットの位置: ({fx:.2f}, {fy:.2f})、向き: {fyaw:.0f} deg")
    if result.get("error"):
        lines += ["", "## エラー", "```", result["error"].strip(), "```"]
    if result.get("log_tail"):
        lines += ["", "## 実行ログ（最後の部分）", "```", *result["log_tail"], "```"]
    lines += ["", "原因を考えて、修正したコード全体を ```python のコードブロック 1 つで出力してください。"]
    return "\n".join(lines)


# ---------------- LLM の応答からコードを取り出す ----------------
def strip_thinking(response: str):
    """思考過程（<think>...</think>）を取り除く。出力が途中で切れて </think> がない場合は <think> 以降をすべて除く."""
    text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    return text.split("<think>")[0] if "<think>" in text else text


def extract_code(response: str):
    """LLM の応答から実行するコードを取り出す。取り出せなければ None."""
    text = strip_thinking(response)
    blocks = re.findall(r"```(?:python|py)?[^\n]*\n(.*?)```", text, flags=re.DOTALL)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    # コードブロックなしでコードだけが貼られた場合は、Python として読めればそのまま使う
    try:
        compile(text, "<generated>", "exec")
    except SyntaxError:
        return None
    return text.strip() + "\n" if text.strip() else None


# ---------------- 実行記録 ----------------
def new_run_dir(label, base_dir=None):
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}_{label}"
    run_dir = Path(base_dir or RUNS_DIR) / run_id
    (run_dir / "attempt_1").mkdir(parents=True)
    return run_dir


def latest_run_dir():
    runs = sorted(p for p in RUNS_DIR.glob("*") if p.is_dir()) if RUNS_DIR.exists() else []
    if not runs:
        raise FileNotFoundError("runs/ に実行記録がありません。先に cap_prompt.py を実行してください。")
    return runs[-1]


def latest_attempt_dir(run_dir: Path):
    attempts = sorted(run_dir.glob("attempt_*"), key=lambda p: int(p.name.split("_")[1]))
    return attempts[-1]


def save_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append_result_row(row, results_csv=None):
    """結果の CSV（既定は results.csv）に 1 行追記する.

    CSV が Excel などで開かれていて書き込めない場合は <名前>_pending.csv に退避し、
    次に書き込めたときにまとめて移す。
    """
    results_csv = Path(results_csv) if results_csv else RESULTS_CSV
    pending_csv = PENDING_CSV if results_csv == RESULTS_CSV else results_csv.with_name(f"{results_csv.stem}_pending.csv")
    rows = []
    if pending_csv.exists():
        with open(pending_csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    rows.append({k: row.get(k, "") for k in RESULTS_FIELDS})
    try:
        is_new = not results_csv.exists()
        # Excel で文字化けしないよう BOM 付き UTF-8 で書く
        with open(results_csv, "a", newline="", encoding="utf-8-sig" if is_new else "utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_FIELDS)
            if is_new:
                writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        with open(pending_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"※ {results_csv.name} が Excel などで開かれているため書き込めませんでした。"
              f"{pending_csv.name} に退避し、次回の実行時に {results_csv.name} へ移します。")
        return
    pending_csv.unlink(missing_ok=True)


def save_trajectory_csv(path, traj):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(traj[0].keys()))
        writer.writeheader()
        writer.writerows(traj)


def plot_trajectory(path, traj, scene: SceneSpec, title):
    """上から見たロボットの軌跡と物体の配置を画像に保存する（レポート用）."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    # インストール済みの日本語フォントを 1 つ選ぶ（存在しないフォント名を並べると警告が大量に出るため）
    installed = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (name for name in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP") if name in installed), "DejaVu Sans"
    )
    fig, ax = plt.subplots(figsize=(7, 6))
    for o in scene.objects:
        ax.add_patch(Rectangle((o.pos[0] - o.size[0] / 2, o.pos[1] - o.size[1] / 2), o.size[0], o.size[1],
                               color=o.color, alpha=0.8))
        ax.annotate(o.name, (o.pos[0], o.pos[1] + o.size[1] / 2 + 0.1), ha="center", fontsize=8)
    xs, ys = [r["x"] for r in traj], [r["y"] for r in traj]
    sc = ax.scatter(xs, ys, c=[r["t"] for r in traj], cmap="viridis", s=4)
    fig.colorbar(sc, ax=ax, label="時刻 [s]")
    ax.plot(xs[0], ys[0], "ko", label="開始")
    ax.plot(xs[-1], ys[-1], "k*", markersize=14, label="終了")
    yaw = math.radians(traj[-1]["yaw_deg"])
    ax.arrow(xs[-1], ys[-1], 0.4 * math.cos(yaw), 0.4 * math.sin(yaw), width=0.03, color="k")
    all_x = xs + [o.pos[0] for o in scene.objects]
    all_y = ys + [o.pos[1] for o in scene.objects]
    ax.set_xlim(min(all_x) - 1.0, max(all_x) + 1.0)
    ax.set_ylim(min(all_y) - 1.0, max(all_y) + 1.0)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(title, fontsize=10)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------- クリップボード（Windows） ----------------
def copy_to_clipboard(path):
    """ファイルの中身をクリップボードにコピーする。成功したら True."""
    if sys.platform != "win32":
        return False
    cmd = f"Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 -LiteralPath '{path}')"
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True).returncode == 0


def read_clipboard():
    if sys.platform != "win32":
        raise RuntimeError("クリップボードの読み取りは Windows のみ対応です。--response でファイルを指定してください。")
    cmd = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw"
    out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
    return out.stdout.decode("utf-8")
