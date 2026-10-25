"""デモ動画（約 2 分、音声なし）を組み立てる.

構成: OP → タイトル → 仕組み → 比べる条件 → T10 を 4 通りで並べた四分割 → 結果
      → 修正依頼で改善した例（Qwen・high の T09、T03） → まとめ → ED

使い方（last_submission/ から、実験側の環境で。先に replay_qwen.py で Qwen の試行を録画しておく）:
    genesis-world/.venv/Scripts/python movie_build/make_movie.py            # 本番（1920x1080）
    genesis-world/.venv/Scripts/python movie_build/make_movie.py --preview  # 確認用（各場面の静止画のみ）
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from moviepy import (ColorClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, concatenate_videoclips,
                     vfx)
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
RUNS = ROOT / "cap_go2" / "runs"
REPLAY = HERE / "replay"
OUT = HERE / "out"

W, H = 1920, 1080
FPS = 30
FONT_R = "C:/Windows/Fonts/BIZ-UDGothicR.ttc"
FONT_B = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"

# 色（レポートの図と同じ配色）
BG = (16, 22, 32)
PANEL = (30, 39, 54)
INK = (242, 244, 247)
MUTED = (160, 170, 186)
BLUE = (42, 120, 214)      # 成功
ORANGE = (235, 104, 52)    # 停滞
GREEN = (27, 175, 122)
YELLOW = (237, 161, 0)     # エラー

FADE = 0.35

# シミュレーションの動画（960x540）のうち、ロボット・壁・箱が映る範囲を切り出して拡大する
CROP = (80, 60, 800, 465)  # (x1, y1, x2, y2)、16:9

VIDEOS = {
    "claude_high_T10": RUNS / "20261024-022732_T10" / "attempt_1" / "video.mp4",
    "claude_low_T10": RUNS / "20261024-033106_T10" / "attempt_1" / "video.mp4",
    "qwen_high_T10": REPLAY / "20261023-164303_T10_high_s0_attempt1" / "attempt_1" / "video.mp4",
    "qwen_low_T10": REPLAY / "20261023-185446_T10_low_s0_attempt1" / "attempt_1" / "video.mp4",
    "qwen_high_T03_a1": REPLAY / "20261023-162535_T03_high_s0_attempt1" / "attempt_1" / "video.mp4",
    "qwen_high_T03_a2": REPLAY / "20261023-162535_T03_high_s0_attempt2" / "attempt_1" / "video.mp4",
}
# T09 はロボットがカメラの画角の外に出るので、記録した軌跡から真上から見た動画を作る
T09_TRAJECTORY = REPLAY / "20261023-164025_T09_high_s0_attempt2" / "attempt_1" / "trajectory.csv"


# ---------------------------------------------------------------- 文字と図形を描く

def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


class Canvas:
    """PIL で 1 枚の画像（RGBA）を描く. 透明な背景にすれば動画の上に重ねられる."""

    def __init__(self, w=W, h=H, bg=BG):
        self.img = Image.new("RGBA", (w, h), bg + (255,) if bg is not None else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, size, color=INK, bold=False, anchor="la", spacing=14):
        self.d.multiline_text(xy, s, font=font(size, bold), fill=color, anchor=anchor, spacing=spacing)

    def text_width(self, s, size, bold=False):
        return self.d.textlength(s, font=font(size, bold))

    def box(self, xy, fill=PANEL, radius=18, outline=None, width=3):
        self.d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

    def arrow(self, x1, y, x2, color=MUTED):
        self.d.line([(x1, y), (x2 - 14, y)], fill=color, width=5)
        self.d.polygon([(x2, y), (x2 - 20, y - 12), (x2 - 20, y + 12)], fill=color)

    def label(self, xy, s, size, fg=INK, bg=(0, 0, 0, 170), pad=(16, 10), bold=True, anchor="lt"):
        """背景付きの短いラベル. anchor は左上 (lt) / 右上 (rt) / 左下 (lb) / 中央下 (mb)."""
        f = font(size, bold)
        x0, y0, x1, y1 = self.d.textbbox((0, 0), s, font=f)
        tw, th = x1 - x0, y1 - y0
        bw, bh = tw + 2 * pad[0], th + 2 * pad[1]
        x, y = xy
        if anchor[0] == "r":
            x -= bw
        elif anchor[0] == "m":
            x -= bw / 2
        if anchor[1] == "b":
            y -= bh
        self.d.rounded_rectangle((x, y, x + bw, y + bh), radius=10, fill=bg)
        self.d.text((x + pad[0] - x0, y + pad[1] - y0), s, font=f, fill=fg)

    def clip(self, duration):
        return ImageClip(np.array(self.img)).with_duration(duration)


def card(duration, draw):
    c = Canvas()
    draw(c)
    return c.clip(duration).with_effects([vfx.FadeIn(FADE), vfx.FadeOut(FADE)])


def heading(c, s, sub=None):
    c.text((120, 100), s, 64, bold=True)
    c.d.line([(120, 196), (300, 196)], fill=BLUE, width=6)
    if sub:
        c.text((120, 226), sub, 34, color=MUTED)


# ---------------------------------------------------------------- 動画の部品

def sim_clip(key, size, speed, length=None):
    """シミュレーションの動画を切り出し・拡大・倍速にする. length（倍速後の秒数）で打ち切る."""
    clip = VideoFileClip(str(VIDEOS[key])).cropped(*CROP).resized(size)
    clip = clip.with_effects([vfx.MultiplySpeed(speed)])
    if length is not None and clip.duration > length:
        clip = clip.subclipped(0, length)
    return clip


def topdown_clip(traj_csv, scene_name, size, speed, bounds):
    """記録した軌跡を、真上から見たアニメーションにする（カメラの画角に収まらない動きのため）.

    bounds: 表示する範囲 (x_min, x_max, y_min, y_max) [m]
    """
    sys.path.insert(0, str(ROOT / "cap_go2"))
    from scenes import SCENES
    with open(traj_csv, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["api_call"] != "(setup)"]
    t = np.array([float(r["t"]) for r in rows])
    t -= t[0]
    xs = np.array([float(r["x"]) for r in rows])
    ys = np.array([float(r["y"]) for r in rows])
    yaws = np.radians([float(r["yaw_deg"]) for r in rows])
    w, h = size
    x_min, x_max, y_min, y_max = bounds
    scale = min(w / (x_max - x_min), h / (y_max - y_min))
    ox = (w - (x_max - x_min) * scale) / 2
    oy = (h - (y_max - y_min) * scale) / 2

    def px(x, y):
        return ox + (x - x_min) * scale, h - oy - (y - y_min) * scale

    base = Canvas(w, h, bg=(26, 36, 52))
    for gx in range(int(np.ceil(x_min)), int(x_max) + 1):
        base.d.line([px(gx, y_min), px(gx, y_max)], fill=(44, 56, 76), width=1)
    for gy in range(int(np.ceil(y_min)), int(y_max) + 1):
        base.d.line([px(x_min, gy), px(x_max, gy)], fill=(44, 56, 76), width=1)
    for obj in SCENES[scene_name].objects:
        (x0, y0), (x1, y1) = px(obj.pos[0] - obj.size[0] / 2, obj.pos[1] + obj.size[1] / 2), \
            px(obj.pos[0] + obj.size[0] / 2, obj.pos[1] - obj.size[1] / 2)
        base.d.rectangle((x0, y0, x1, y1), fill=tuple(int(255 * v) for v in obj.color))
    sx, sy = px(xs[0], ys[0])
    base.d.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=INK, width=3)
    base.label((w - 14, 14), "真上から見た軌跡（1 マス = 1 m）", 22, bold=False, anchor="rt")
    base_img = base.img

    def frame(tau):
        n = max(int(np.searchsorted(t, tau * speed, side="right")), 1)
        img = base_img.copy()
        d = ImageDraw.Draw(img)
        pts = [px(x, y) for x, y in zip(xs[:n], ys[:n])]
        if len(pts) > 1:
            d.line(pts, fill=BLUE, width=5, joint="curve")
        cx, cy = pts[-1]
        a = yaws[n - 1]
        tri = [(cx + 20 * np.cos(a), cy - 20 * np.sin(a)),
               (cx + 12 * np.cos(a + 2.5), cy - 12 * np.sin(a + 2.5)),
               (cx + 12 * np.cos(a - 2.5), cy - 12 * np.sin(a - 2.5))]
        d.polygon(tri, fill=INK)
        return np.array(img.convert("RGB"))

    return VideoClip(frame_function=frame, duration=t[-1] / speed)


def hold(clip, total):
    """clip の最後の画面で止め、全体を total 秒にする."""
    if clip.duration >= total:
        return clip.subclipped(0, total)
    last = ImageClip(clip.get_frame(clip.duration - 1 / FPS)).with_duration(total - clip.duration)
    return concatenate_videoclips([clip, last])


def overlay(size, draw):
    c = Canvas(*size, bg=None)
    draw(c)
    return np.array(c.img)


def panel(source, size, speed, total, title, result, result_color, cut=None, cut_note=None):
    """1 つの画面: 動画 + 左上の条件名 + 再生し終えたら結果のラベル.

    source: VIDEOS のキー（シミュレーションの動画）か、size に合わせて作った動画（倍速は適用済み）
    """
    w, h = size
    video = sim_clip(source, size, speed, cut) if isinstance(source, str) else source
    ended = video.duration
    video = hold(video, total)
    top = ImageClip(overlay(size, lambda c: c.label((14, 14), title, 30))).with_duration(total)

    def draw_result(c):
        if cut_note:
            c.label((w - 14, 14), cut_note, 22, fg=INK, bold=False, anchor="rt")
        c.label((w / 2, h - 18), result, 30, bg=result_color + (235,), anchor="mb")

    res = ImageClip(overlay(size, draw_result)).with_start(ended).with_duration(total - ended)
    return CompositeVideoClip([video, top, res], size=size).with_duration(total)


# ---------------------------------------------------------------- 各場面

def scene_title():
    def draw(c):
        c.text((W / 2, 400), "自然言語指示による四足歩行ロボットの制御", 76, bold=True, anchor="mm")
        c.text((W / 2, 500), "強化学習の歩行方策と Code as Policies の階層化", 46, color=MUTED, anchor="mm")
        c.d.line([(W / 2 - 160, 580), (W / 2 + 160, 580)], fill=BLUE, width=5)
        c.text((W / 2, 660), "PAI2026_応用Ⅰ 最終課題", 36, anchor="mm")
    return card(5.0, draw)


def scene_system():
    def draw(c):
        heading(c, "仕組み", "LLM が「どこへ・どう動くか」をコードで決め、足の動かし方は強化学習の方策が担う")
        boxes = [
            ("自然言語の指示", "「赤い箱まで行って」"),
            ("LLM", "claude.ai / Qwen3-4B"),
            ("Python コード", "ロボットの API を呼ぶ"),
            ("歩行方策", "強化学習（PPO）\n速度指令 → 関節"),
            ("Go2", "Genesis 上で実行"),
        ]
        bw, gap, y0, bh = 300, 52, 420, 210
        x = (W - (5 * bw + 4 * gap)) / 2
        for i, (t, s) in enumerate(boxes):
            c.box((x, y0, x + bw, y0 + bh), outline=BLUE if i in (1, 2) else None)
            c.text((x + bw / 2, y0 + 62), t, 40, bold=True, anchor="mm")
            c.text((x + bw / 2, y0 + 140), s, 27, color=MUTED, anchor="mm", spacing=10)
            if i < 4:
                c.arrow(x + bw + 6, y0 + bh / 2, x + bw + gap - 6)
            x += bw + gap
        c.text((W / 2, 780), "失敗したら、失敗の種類・最終位置・ログを LLM に返して、コードを直させる（最大 3 回）",
               34, anchor="mm")
        c.text((W / 2, 850), "18 個のタスクを用意し、成否は自動で判定する", 34, color=MUTED, anchor="mm")
    return card(9.0, draw)


def scene_conditions():
    def draw(c):
        heading(c, "比べる条件", "LLM 2 種類 × API の抽象度 2 段階 = 4 通り")
        cols = [
            ("LLM", [("claude.ai（Opus 5.5）", ""), ("Qwen3-4B-Instruct", "小型のオープンウェイトモデル、事後学習なし")]),
            ("API の抽象度", [("high", "move_to(x, y)・turn・face など"), ("low", "walk(速度)・stop と、位置・向きの取得のみ")]),
        ]
        for i, (t, items) in enumerate(cols):
            x = 120 + i * 860
            c.text((x, 340), t, 44, bold=True)
            for j, (a, b) in enumerate(items):
                y = 430 + j * 170
                c.box((x, y, x + 800, y + 140))
                c.text((x + 36, y + 30), a, 40, bold=True)
                if b:
                    c.text((x + 36, y + 88), b, 28, color=MUTED)
        c.text((120, 820), "どの条件のプロンプトにも、ロボットの大きさ（胴体の前後の半長 0.35 m・左右の半幅 0.15 m）を書いた",
               32)
    return card(8.0, draw)


def scene_task_intro():
    def draw(c):
        c.text((W / 2, 380), "タスク T10", 44, color=MUTED, anchor="mm")
        c.text((W / 2, 500), "「壁にぶつからないように避けて、赤い箱まで行って。」", 64, bold=True, anchor="mm")
        c.text((W / 2, 640), "同じ指示を 4 通りの条件で実行した、1 回目の試行を並べる（4 倍速）", 36, color=MUTED, anchor="mm")
    return card(5.0, draw)


def scene_quad():
    total, speed, cut = 22.0, 4.0, 17.0
    qw, qh = 848, 477
    gap = 14
    x0 = (W - (2 * qw + gap)) / 2
    y0 = 96
    stall = "失敗：壁に押し付けたまま前進し続けた"
    panels = [
        ("claude_high_T10", "claude.ai × high", "成功：壁を回り込んで箱の手前で停止", BLUE, None),
        ("claude_low_T10", "claude.ai × low", "成功：壁を回り込んで箱の手前で停止", BLUE, None),
        ("qwen_high_T10", "Qwen3-4B × high", stall, ORANGE, None),
        ("qwen_low_T10", "Qwen3-4B × low", stall, ORANGE, "以降も同じ状態が続く（計 102 秒）"),
    ]
    layers = [ColorClip((W, H), color=BG).with_duration(total)]
    for i, (key, title, result, color, note) in enumerate(panels):
        p = panel(key, (qw, qh), speed, total, title, result, color, cut=cut, cut_note=note)
        layers.append(p.with_position((x0 + (i % 2) * (qw + gap), y0 + (i // 2) * (qh + gap))))
    head = Canvas(bg=None)
    head.text((W / 2, 50), "T10「壁にぶつからないように避けて、赤い箱まで行って。」　4 倍速", 36, bold=True, anchor="mm")
    layers.append(ImageClip(np.array(head.img)).with_duration(total))
    return CompositeVideoClip(layers, size=(W, H)).with_duration(total).with_effects([vfx.FadeIn(FADE), vfx.FadeOut(FADE)])


def scene_results():
    def draw(c):
        heading(c, "18 タスクの結果", "成功したタスクの数（修正依頼を含めて最大 3 回の試行）")
        rows = [("claude.ai", 18, 18), ("Qwen3-4B", 7, 2)]
        x, y = 160, 330
        c.text((x + 420, y), "high", 40, bold=True, anchor="ma")
        c.text((x + 700, y), "low", 40, bold=True, anchor="ma")
        for j, (name, hi, lo) in enumerate(rows):
            yy = y + 90 + j * 110
            c.box((x - 30, yy - 20, x + 830, yy + 80))
            c.text((x, yy + 30), name, 40, bold=True, anchor="lm")
            for k, v in ((420, hi), (700, lo)):
                c.text((x + k, yy + 30), f"{v} / 18", 48, bold=True, color=BLUE if v == 18 else INK, anchor="mm")
        rx = 1080
        c.box((rx, 330, 1800, 900), outline=ORANGE)
        c.text((rx + 40, 370), "Qwen3-4B の失敗の内訳", 36, bold=True)
        c.text((rx + 40, 440), "失敗 83 試行のうち 46 試行（55%）が\n物体に押し付けたままの停滞", 34, spacing=16)
        c.text((rx + 40, 580), "46 試行のうち 34 試行のコードは\nロボットの大きさに触れていた", 34, spacing=16)
        c.text((rx + 40, 720), "「表面から 0.35 m」を「中心から 0.35 m」\nと取り違えるなど、計算に正しく\n使えていなかった", 30,
               color=MUTED, spacing=14)
    return card(10.0, draw)


def scene_retry_intro():
    def draw(c):
        heading(c, "修正依頼で改善した例", "Qwen3-4B × high で、2 回目の試行で成功に変わった 2 タスク")
        c.text((120, 360), "失敗した試行のあとに、次の内容を LLM に返してコードを直させる", 40, bold=True)
        for i, s in enumerate(["失敗の種類（構文エラー・実行時エラー・停滞・未達成 など）",
                               "エラーの起きた行と内容、判定の詳細",
                               "実行後のロボットの位置と向き、実行ログの最後の部分"]):
            y = 470 + i * 90
            c.d.ellipse((140, y + 10, 160, y + 30), fill=BLUE)
            c.text((190, y), s, 36)
    return card(7.0, draw)


def scene_feedback_intro():
    def draw(c):
        heading(c, "T03「赤い箱のところまで行って。」", "Qwen3-4B × high")
        c.text((120, 340), "試行 1 のあとに LLM へ返した修正依頼（抜粋）", 34, color=MUTED)
        c.box((120, 400, 1800, 700), outline=ORANGE)
        c.text((170, 440),
               "失敗の種類: 停滞（物体に押し付け）\n"
               "詳細: 移動の指令を出しているのにほとんど動けなかった時間が合計 25.0 秒あった\n"
               "（基準 3 秒以下）。箱や壁にぶつかったまま前進し続けた可能性がある\n"
               "実行後のロボットの位置: (2.51, -0.01)、向き: 3 deg", 34, spacing=22)
        c.text((120, 770), "→ 試行 2 では、目標を箱の中心ではなく、中心から 0.35 m 手前に置き直した", 36, bold=True)
    return card(9.0, draw)


def scene_t03():
    total, speed = 12.0, 4.0
    pw, ph = 920, 518
    gap = 20
    x0 = (W - (2 * pw + gap)) / 2
    y0 = 170
    layers = [ColorClip((W, H), color=BG).with_duration(total)]
    a1 = panel("qwen_high_T03_a1", (pw, ph), speed, total, "試行 1：箱の中心へ move_to",
               "失敗：箱に押し付けたまま 25 秒前進し続けた", ORANGE)
    a2 = panel("qwen_high_T03_a2", (pw, ph), speed, total, "試行 2：目標を箱の中心から 0.35 m 手前に",
               "成功：箱に触れたところで停止", BLUE)
    layers += [a1.with_position((x0, y0)), a2.with_position((x0 + pw + gap, y0))]
    c = Canvas(bg=None)
    c.text((W / 2, 90), "T03「赤い箱のところまで行って。」　Qwen3-4B × high　4 倍速", 40, bold=True, anchor="mm")
    c.text((W / 2, 780), "止まれるようにはなったが、止まった位置はどちらも箱に接する位置（箱の中心から約 0.49 m）", 34,
           bold=True, anchor="mm")
    c.text((W / 2, 845), "目標の「箱の中心から 0.35 m」は、胴体の前半分（0.35 m）が箱に重なる位置。", 30, color=MUTED, anchor="mm")
    c.text((W / 2, 895), "move_to の許容誤差（0.15 m）の範囲に入ったので止まれただけで、止まる位置の計算は直っていない", 30,
           color=MUTED, anchor="mm")
    layers.append(ImageClip(np.array(c.img)).with_duration(total))
    return CompositeVideoClip(layers, size=(W, H)).with_duration(total).with_effects([vfx.FadeIn(FADE), vfx.FadeOut(FADE)])


def scene_t09():
    total, speed = 13.0, 8.0
    pw, ph = 920, 518
    gap = 20
    x0 = (W - (2 * pw + gap)) / 2
    y0 = 170
    layers = [ColorClip((W, H), color=BG).with_duration(total)]
    path = topdown_clip(T09_TRAJECTORY, "basic", (pw, ph), speed, bounds=(-4.2, 4.2, -3.0, 7.2))
    a2 = panel(path, (pw, ph), speed, total, "試行 2：while ループに書き直す",
               "成功：一周して元の場所の近くに戻った", BLUE)
    layers.append(a2.with_position((x0 + pw + gap, y0)))
    c = Canvas(bg=None)
    c.text((W / 2, 90), "T09「左回りに円を描くように一周して、元の場所付近に戻って。」　Qwen3-4B × high　8 倍速", 36,
           bold=True, anchor="mm")
    c.box((x0, y0, x0 + pw, y0 + ph), fill=PANEL + (255,), outline=YELLOW)
    c.text((x0 + 40, y0 + 40), "試行 1：実行時エラー", 40, bold=True, color=YELLOW)
    c.text((x0 + 40, y0 + 130), "for angle in range(0, total_angle + 1, angle_step):", 26, color=INK)
    c.text((x0 + 40, y0 + 200), "TypeError: 'float' object cannot be\ninterpreted as an integer", 28, color=MUTED, spacing=12)
    c.text((x0 + 40, y0 + 330), "エラーの行と内容を返すと、角度を小数の\nまま増やす while ループに直した", 32, spacing=14)
    c.text((W / 2, 780), "試行 2 は「10° 旋回して 0.5 m 前進」をくり返し、大きな円を描いて始点の近くに戻った", 34,
           bold=True, anchor="mm")
    c.text((W / 2, 845), "（コードでは半径 1 m としていたが、その値は動きに使われておらず、実際の半径は約 3 m）", 30, color=MUTED,
           anchor="mm")
    layers.append(ImageClip(np.array(c.img)).with_duration(total))
    return CompositeVideoClip(layers, size=(W, H)).with_duration(total).with_effects([vfx.FadeIn(FADE), vfx.FadeOut(FADE)])


def scene_summary():
    def draw(c):
        heading(c, "まとめ")
        items = [
            ("claude.ai は、API の抽象度によらず 18 タスクすべてを 1 回目で達成した",
             "low では move_to などに相当する関数をタスクごとに自作し直し、コードが約 1.6 倍に増えた"),
            ("Qwen3-4B は、ロボットの大きさを与えても物体に押し付けたまま前進し続けた",
             "情報を書くことと、モデルがそれを推論に使えることは別"),
        ]
        for i, (a, b) in enumerate(items):
            y = 290 + i * 210
            c.d.ellipse((120, y + 4, 160, y + 44), fill=BLUE)
            c.text((140, y + 24), str(i + 1), 28, bold=True, anchor="mm")
            c.text((190, y), a, 40, bold=True)
            c.text((190, y + 70), b, 30, color=MUTED)
    return card(11.0, draw)


def jingle(name):
    return VideoFileClip(str(ROOT / "movie" / name)).resized((W, H)).without_audio()


SCENES = [scene_title, scene_system, scene_conditions, scene_task_intro, scene_quad, scene_results,
          scene_retry_intro, scene_t09, scene_feedback_intro, scene_t03, scene_summary]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="各場面の途中の静止画だけを書き出す")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.preview:
        for i, make in enumerate(SCENES):
            clip = make()
            for frac in ((0.5,) if isinstance(clip, ImageClip) or "intro" in make.__name__ else (0.25, 0.95)):
                Image.fromarray(clip.get_frame(clip.duration * frac)[..., :3].astype(np.uint8)).save(
                    OUT / f"preview_{i:02d}_{make.__name__}_{int(frac * 100)}.png")
            print(f"{make.__name__}: {clip.duration:.1f} s")
        return
    clips = [jingle("PAI応用1_最終課題_OP.mp4")] + [make() for make in SCENES] + [jingle("PAI応用1_最終課題_ED.mp4")]
    movie = concatenate_videoclips(clips, method="compose")
    print(f"全体: {movie.duration:.1f} s")
    movie.write_videofile(str(OUT / "PAI応用1_最終課題_demo.mp4"), fps=FPS, codec="libx264", audio=False,
                          preset="medium", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"])


if __name__ == "__main__":
    main()
