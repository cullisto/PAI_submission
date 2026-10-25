"""学習ログ（TensorBoard のイベントファイル）から学習曲線の図を作る（レポート・動画用）.

使い方:
    python plot_training_curves.py go2-omni            # src_ext/logs/go2-omni を読む
出力: report_assets/training_curves_<実験名>.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

ROOT = Path(__file__).resolve().parents[1]

PANELS = [
    ("Train/mean_reward", "平均報酬（合計）", None),
    ("Episode/rew_tracking_lin_vel", "速度指令への追従（並進）", 1.0),
    ("Episode/rew_tracking_ang_vel", "速度指令への追従（旋回）", 0.5),
    ("Policy/mean_noise_std", "行動ノイズの標準偏差（探索の大きさ）", None),
]


def main():
    exp_name = sys.argv[1] if len(sys.argv) > 1 else "go2-omni"
    log_dir = ROOT / "src_ext" / "logs" / exp_name
    ea = EventAccumulator(str(log_dir))
    ea.Reload()

    # インストール済みの日本語フォントを 1 つ選ぶ（存在しないフォント名を並べると警告が大量に出るため）
    installed = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (name for name in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP") if name in installed), "DejaVu Sans"
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (tag, title, max_value) in zip(axes.flat, PANELS):
        events = ea.Scalars(tag)
        ax.plot([e.step for e in events], [e.value for e in events])
        if max_value is not None:
            ax.axhline(max_value, color="gray", linestyle="--", linewidth=1, label=f"最大値 {max_value}")
            ax.legend(fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("学習イテレーション")
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"Go2 歩行方策の学習曲線（{exp_name}）")
    fig.tight_layout()
    out_dir = ROOT / "report_assets"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"training_curves_{exp_name}.png"
    fig.savefig(out_path, dpi=150)
    print(out_path)


if __name__ == "__main__":
    main()
