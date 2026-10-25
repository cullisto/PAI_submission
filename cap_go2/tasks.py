"""評価用タスク（自然言語指示と成功判定）.

成功判定は、生成コードの実行後にロボットが静止したときの状態と、実行中の軌跡から自動で行う。
"""

import math
from dataclasses import dataclass
from itertools import permutations
from typing import Callable

from scenes import SCENES, SceneSpec

REACH_DIST = 0.7  # 箱に「着いた」とみなす、ロボット中心と箱中心の距離 [m]（箱の半幅 0.15 + ロボットの半長 約0.35 + 余裕）
ROBOT_RADIUS = 0.25  # 障害物との衝突判定に使うロボットの半径 [m]
STALL_LIMIT_S = 3.0  # 移動指令を出しているのに動けない時間の合計がこれを超えたら失敗（物体に押し付けている）


def stall_time(traj, dt=0.02):
    """移動の指令（0.15 m/s 以上）を出しているのに、実際の速さが 0.05 m/s 未満だった時間の合計 [s].

    箱や壁に押し付けたまま前進し続けると長くなる。最終位置だけを見る判定では見逃すため、全タスク共通で調べる。
    """
    total = 0.0
    for a, b in zip(traj, traj[1:]):
        cmd = math.hypot(b["cmd_vx"], b["cmd_vy"])
        speed = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / dt
        if cmd >= 0.15 and speed < 0.05:
            total += dt
    return total


@dataclass(frozen=True)
class Task:
    task_id: str
    scene: str
    instruction: str
    category: str  # 指示の種類（レポートでの分析用）
    check: Callable  # check(traj, scene) -> (success: bool, detail: str)


# ---- 判定用の補助関数 ----
def obj_pos(scene: SceneSpec, name):
    return next(o.pos for o in scene.objects if o.name == name)


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def final_xy(traj):
    return traj[-1]["x"], traj[-1]["y"]


def start_xy(traj):
    return traj[0]["x"], traj[0]["y"]


def yaw_diff_deg(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def first_index(traj, cond):
    return next((i for i, row in enumerate(traj) if cond(row)), None)


def total_yaw_change_deg(traj):
    """軌跡全体での向きの累積変化 [deg]（左回りが正）."""
    return sum(yaw_diff_deg(b["yaw_deg"], a["yaw_deg"]) for a, b in zip(traj, traj[1:]))


def obstacle_clearance(traj, scene):
    """軌跡上でロボット中心と障害物の表面との最小距離 [m]（障害物がなければ inf）."""
    best = math.inf
    for o in scene.objects:
        if not o.is_obstacle:
            continue
        hx, hy = o.size[0] / 2, o.size[1] / 2
        for row in traj:
            dx = max(abs(row["x"] - o.pos[0]) - hx, 0.0)
            dy = max(abs(row["y"] - o.pos[1]) - hy, 0.0)
            best = min(best, math.hypot(dx, dy))
    return best


def check_reach(name, threshold=REACH_DIST):
    def check(traj, scene):
        d = dist(final_xy(traj), obj_pos(scene, name))
        return d < threshold, f"{name} までの最終距離 {d:.2f} m（基準 < {threshold} m）"

    return check


def check_point(target, threshold=0.4, yaw_deg=None, yaw_tol=20.0):
    def check(traj, scene):
        d = dist(final_xy(traj), target)
        ok = d < threshold
        detail = f"目標点 {target} までの最終距離 {d:.2f} m（基準 < {threshold} m）"
        if yaw_deg is not None:
            e = abs(yaw_diff_deg(traj[-1]["yaw_deg"], yaw_deg))
            ok = ok and e < yaw_tol
            detail += f"、向きの誤差 {e:.0f} deg（基準 < {yaw_tol} deg）"
        return ok, detail

    return check


# ---- 個別の判定 ----
def check_turn_left_90(traj, scene):
    e = abs(yaw_diff_deg(traj[-1]["yaw_deg"], traj[0]["yaw_deg"] + 90.0))
    moved = dist(final_xy(traj), start_xy(traj))
    return e < 15.0 and moved < 0.4, f"90度からの誤差 {e:.0f} deg（基準 < 15）、移動距離 {moved:.2f} m（基準 < 0.4）"


def check_blue_then_green(traj, scene):
    blue, green = obj_pos(scene, "blue_box"), obj_pos(scene, "green_box")
    i_blue = first_index(traj, lambda r: dist((r["x"], r["y"]), blue) < REACH_DIST + 0.1)
    d_green = dist(final_xy(traj), green)
    ok = i_blue is not None and d_green < REACH_DIST
    return ok, f"青い箱に寄った: {'はい' if i_blue is not None else 'いいえ'}、緑の箱までの最終距離 {d_green:.2f} m"


def check_square(traj, scene):
    back = dist(final_xy(traj), start_xy(traj))
    xs, ys = [r["x"] for r in traj], [r["y"] for r in traj]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    ok = back < 0.4 and 0.7 < w < 1.4 and 0.7 < h < 1.4
    return ok, f"始点までの距離 {back:.2f} m（基準 < 0.4）、軌跡の幅 {w:.2f} m × {h:.2f} m（基準 0.7〜1.4）"


def check_nearest_box(traj, scene):
    start = start_xy(traj)
    nearest = min((o for o in scene.objects if not o.is_obstacle), key=lambda o: dist(start, o.pos))
    d = dist(final_xy(traj), nearest.pos)
    return d < REACH_DIST, f"最も近い箱は {nearest.name}、その箱までの最終距離 {d:.2f} m（基準 < {REACH_DIST}）"


def check_midpoint(traj, scene):
    r, b = obj_pos(scene, "red_box"), obj_pos(scene, "blue_box")
    return check_point(((r[0] + b[0]) / 2, (r[1] + b[1]) / 2))(traj, scene)


def check_circle_left(traj, scene):
    back = dist(final_xy(traj), start_xy(traj))
    turned = total_yaw_change_deg(traj)
    radius = max(dist((r["x"], r["y"]), start_xy(traj)) for r in traj)
    ok = back < 0.6 and turned > 300.0 and radius > 0.5
    return ok, (f"始点までの距離 {back:.2f} m（基準 < 0.6）、左回りの累積回転 {turned:.0f} deg（基準 > 300）、"
                f"始点から最も離れた距離 {radius:.2f} m（基準 > 0.5）")


def check_reach_avoiding(name):
    def check(traj, scene):
        reached, detail = check_reach(name)(traj, scene)
        clearance = obstacle_clearance(traj, scene)
        ok = reached and clearance > ROBOT_RADIUS
        return ok, f"{detail}、障害物との最小距離 {clearance:.2f} m（基準 > {ROBOT_RADIUS} m、これ以下は衝突）"

    return check


# ---- 難しいタスク（H01〜H07）の判定 ----
def bearing_deg(p, q):
    """点 p から点 q への方角 [deg]."""
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def path_length(traj):
    """軌跡の長さ [m]（足踏みによる細かな揺れを拾わないよう 0.2 秒ごとに間引いて測る）."""
    thinned = traj[::10] + [traj[-1]]
    return sum(dist((a["x"], a["y"]), (b["x"], b["y"])) for a, b in zip(thinned, thinned[1:]))


def check_behind_blue(traj, scene):
    """青い箱をはさんでスタート地点の反対側に立ち、青い箱の方を向いているか."""
    blue, start, final = obj_pos(scene, "blue_box"), start_xy(traj), final_xy(traj)
    # 箱から見たスタート地点の方角と、箱から見た最終位置の方角の差（180 deg なら真裏）
    side_err = abs(yaw_diff_deg(bearing_deg(blue, final), bearing_deg(blue, start) + 180.0))
    d = dist(final, blue)
    face_err = abs(yaw_diff_deg(traj[-1]["yaw_deg"], bearing_deg(final, blue)))
    ok = side_err < 45.0 and d < 1.0 and face_err < 25.0
    return ok, (f"真裏からのずれ {side_err:.0f} deg（基準 < 45）、青い箱までの距離 {d:.2f} m（基準 < 1.0）、"
                f"箱の方向と向きの差 {face_err:.0f} deg（基準 < 25）")


def tour_length(start, points):
    """start → points の順 → start と回ったときの直線距離の合計."""
    route = (start, *points, start)
    return sum(dist(a, b) for a, b in zip(route, route[1:]))


def check_tour(traj, scene):
    """すべての箱に寄ってスタート地点に戻り、回った順番がほぼ最短か.

    ロボットは箱の手前で止まるため実際の経路は箱の中心を結んだ巡回路より短くなる。経路長そのものでは順番の良し悪しを
    区別できないので、「最初に寄った順番」で箱の中心を結んだ長さを、最短の順番の長さと比べる。
    """
    boxes = [o for o in scene.objects if not o.is_obstacle]
    start = start_xy(traj)
    first_visit = {o.name: first_index(traj, lambda r, o=o: dist((r["x"], r["y"]), o.pos) < REACH_DIST + 0.1)
                   for o in boxes}
    visited = sorted((i, name) for name, i in first_visit.items() if i is not None)
    back = dist(final_xy(traj), start)
    best = min(tour_length(start, [o.pos for o in order]) for order in permutations(boxes))
    detail = (f"寄った順番 {' → '.join(name for _, name in visited) or 'なし'}（{len(visited)}/{len(boxes)} 個）、"
              f"始点までの距離 {back:.2f} m（基準 < 0.5）")
    if len(visited) < len(boxes):
        return False, detail
    order_length = tour_length(start, [obj_pos(scene, name) for _, name in visited])
    length = path_length(traj)
    ok = back < 0.5 and order_length <= 1.05 * best and length < 1.2 * best
    return ok, (f"{detail}、この順番の巡回路 {order_length:.2f} m（最短 {best:.2f} m の 1.05 倍以内）、"
                f"実際の経路長 {length:.1f} m（基準 < {1.2 * best:.1f} m）")


def check_through_gap(traj, scene):
    """壁の隙間（y = 0.55〜1.45）を通って壁の向こうの赤い箱に着いたか."""
    wall_x = 2.0
    crossings = [(a["y"] + b["y"]) / 2 for a, b in zip(traj, traj[1:]) if (a["x"] - wall_x) * (b["x"] - wall_x) <= 0 < abs(b["x"] - a["x"])]
    through_gap = bool(crossings) and all(0.55 < y < 1.45 for y in crossings)
    reached, detail = check_reach("red_box")(traj, scene)
    clearance = obstacle_clearance(traj, scene)
    ok = through_gap and reached and clearance > 0.2
    crossing_text = ", ".join(f"{y:.2f}" for y in crossings) or "なし"
    return ok, (f"壁の線を横切った位置 y = {crossing_text}（隙間は 0.55〜1.45）、{detail}、"
                f"壁との最小距離 {clearance:.2f} m（基準 > 0.2 m）")


def check_keep_away(name, min_dist):
    def check(traj, scene):
        reached, detail = check_reach("red_box")(traj, scene)
        closest = min(dist((r["x"], r["y"]), obj_pos(scene, name)) for r in traj)
        ok = reached and closest > min_dist
        return ok, f"{detail}、{name} の中心との最小距離 {closest:.2f} m（基準 > {min_dist} m）"

    return check


def check_back_to_red(traj, scene):
    """赤い箱から約 1 m の位置で、箱にお尻（後ろ側）を向けているか."""
    red, final = obj_pos(scene, "red_box"), final_xy(traj)
    d = dist(final, red)
    # 向いている方向と「箱の方向」の差が 180 deg なら、お尻が箱を向いている
    back_err = abs(yaw_diff_deg(traj[-1]["yaw_deg"], bearing_deg(final, red) + 180.0))
    ok = 0.75 < d < 1.25 and back_err < 25.0
    return ok, f"赤い箱の中心までの距離 {d:.2f} m（基準 0.75〜1.25）、お尻の向きのずれ {back_err:.0f} deg（基準 < 25）"


def check_strafe_to_blue(traj, scene):
    """向きをほとんど変えずに青い箱の手前まで行ったか."""
    yaw0 = traj[0]["yaw_deg"]
    max_turn = max(abs(yaw_diff_deg(r["yaw_deg"], yaw0)) for r in traj)
    reached, detail = check_reach("blue_box")(traj, scene)
    ok = reached and max_turn < 15.0
    return ok, f"{detail}、最初の向きからの最大のずれ {max_turn:.0f} deg（基準 < 15）"


TASKS = {
    t.task_id: t
    for t in [
        Task("T01", "basic", "前に2メートル進んで止まって。", "基本動作", check_point((2.0, 0.0))),
        Task("T02", "basic", "その場で左に90度回転して。", "基本動作", check_turn_left_90),
        Task("T03", "basic", "赤い箱のところまで行って。", "物体への移動", check_reach("red_box")),
        Task("T04", "basic", "青い箱に寄ってから、緑の箱まで行って。", "複数ステップ", check_blue_then_green),
        Task("T05", "basic", "1辺1メートルの正方形を描くように歩いて、元の場所に戻って。", "軌跡生成", check_square),
        Task("T06", "basic", "一番近い箱まで行って。", "空間推論", check_nearest_box),
        Task("T07", "basic", "1メートル後ろに下がってから、右を向いて。", "複数ステップ", check_point((-1.0, 0.0), yaw_deg=-90.0)),
        Task("T08", "basic", "赤い箱と青い箱のちょうど中間の地点に移動して。", "空間推論", check_midpoint),
        Task("T09", "basic", "左回りに円を描くように一周して、元の場所付近に戻って。", "軌跡生成", check_circle_left),
        Task("T10", "obstacle", "壁にぶつからないように避けて、赤い箱まで行って。", "障害物回避", check_reach_avoiding("red_box")),
        Task("T11", "obstacle", "赤い箱まで行って。", "障害物回避（暗黙）", check_reach_avoiding("red_box")),
        # ---- 難しいタスク ----
        Task("H01", "basic", "青い箱の裏側（スタート地点から見て反対側）に回り込んで、青い箱の方を向いて止まって。",
             "難: 物体基準の位置", check_behind_blue),
        Task("H02", "basic", "すべての箱に1回ずつ寄ってから、スタート地点に戻って。なるべく短い経路で回って。",
             "難: 経路の最適化", check_tour),
        Task("H03", "gap", "2枚の壁の隙間を通り抜けて、向こう側の赤い箱まで行って。", "難: 狭い隙間", check_through_gap),
        Task("H04", "maze", "赤い箱まで行って。", "難: 多段の経路計画", check_reach_avoiding("red_box")),
        Task("H05", "danger", "紫の箱（危険物）の中心から1.5メートル以内に入らないようにして、赤い箱まで行って。",
             "難: 距離の制約", check_keep_away("purple_box", 1.5)),
        Task("H06", "basic", "赤い箱にお尻を向けて、箱から1メートル離れた位置で止まって。", "難: 向きの解釈", check_back_to_red),
        Task("H07", "basic", "向きを変えずに（その場での旋回もせずに）、前後の移動と横歩きだけで青い箱の手前まで行って。",
             "難: 移動方法の制約", check_strafe_to_blue),
    ]
}


def get_scene_for(task_id=None, scene_name=None):
    if task_id is not None:
        return SCENES[TASKS[task_id].scene]
    return SCENES[scene_name or "basic"]
