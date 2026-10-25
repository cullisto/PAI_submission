"""Code as Policies 用のシーン定義.

座標系: ワールド座標 [m]。x 軸が前方（ロボットの初期の向き）、y 軸が左、z 軸が上。
向き(yaw) は x 軸から反時計回り（左回り）が正の角度 [deg]。
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SceneObject:
    name: str  # LLM に見せる名前（例: "red_box"）
    description: str  # LLM に見せる説明（例: "赤い箱"）
    pos: tuple[float, float]  # 中心の xy 座標 [m]
    size: tuple[float, float, float]  # 箱の大きさ (x, y, z) [m]
    color: tuple[float, float, float]  # RGB (0-1)
    is_obstacle: bool = False  # True なら障害物（ぶつからないように避けるべき物体）


@dataclass(frozen=True)
class SceneSpec:
    name: str
    description: str
    objects: tuple[SceneObject, ...] = field(default_factory=tuple)
    robot_start: tuple[float, float] = (0.0, 0.0)  # ロボットの初期位置 (x, y) [m]
    robot_start_yaw_deg: float = 0.0  # ロボットの初期の向き [deg]
    camera_pos: tuple[float, float, float] = (-2.5, -4.5, 5.0)  # 録画用カメラの位置
    camera_lookat: tuple[float, float, float] = (1.0, 0.0, 0.0)  # 録画用カメラの注視点


BOX = (0.3, 0.3, 0.3)

SCENES = {
    "basic": SceneSpec(
        name="basic",
        description="平らな床に色の違う4つの箱が置かれた部屋",
        objects=(
            SceneObject("red_box", "赤い箱", (3.0, 0.0), BOX, (0.9, 0.1, 0.1)),
            SceneObject("blue_box", "青い箱", (2.0, 2.0), BOX, (0.1, 0.3, 0.9)),
            SceneObject("green_box", "緑の箱", (0.5, -2.5), BOX, (0.1, 0.7, 0.2)),
            SceneObject("yellow_box", "黄色い箱", (-2.0, 1.0), BOX, (0.95, 0.85, 0.1)),
        ),
    ),
    "obstacle": SceneSpec(
        name="obstacle",
        description="ゴールの赤い箱の手前に、横長の灰色の障害物（壁）がある部屋",
        objects=(
            SceneObject("red_box", "赤い箱（ゴール）", (4.0, 0.0), BOX, (0.9, 0.1, 0.1)),
            SceneObject("wall", "灰色の壁（障害物）", (2.0, 0.0), (0.3, 1.6, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
        ),
        camera_pos=(-1.5, -5.0, 5.5),
        camera_lookat=(2.0, 0.0, 0.0),
    ),
    # ---- 難しいタスク用（H03〜H05） ----
    "gap": SceneSpec(
        name="gap",
        description="x = 2.0 m の位置に 2 枚の灰色の壁が y 方向に並び、その間に幅 0.9 m の隙間がある部屋。壁の向こう側に赤い箱がある",
        objects=(
            SceneObject("red_box", "赤い箱（ゴール）", (4.0, -1.0), BOX, (0.9, 0.1, 0.1)),
            # 隙間は y = 0.55〜1.45（中心 y = 1.0）
            SceneObject("wall_upper", "灰色の壁（上側）", (2.0, 2.725), (0.3, 2.55, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
            SceneObject("wall_lower", "灰色の壁（下側）", (2.0, -1.475), (0.3, 4.05, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
        ),
        camera_pos=(-1.5, -6.0, 6.5),
        camera_lookat=(2.0, 0.0, 0.0),
    ),
    "maze": SceneSpec(
        name="maze",
        description="3 枚の灰色の壁がコの字形に並んでいる部屋。コの字の開いた側はロボットの方を向いており、赤い箱はコの字の奥の壁の外側にある",
        objects=(
            SceneObject("red_box", "赤い箱（ゴール）", (4.2, 0.0), BOX, (0.9, 0.1, 0.1)),
            SceneObject("wall_back", "灰色の壁（奥）", (3.0, 0.0), (0.3, 2.7, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
            SceneObject("wall_left", "灰色の壁（左）", (2.325, 1.2), (1.65, 0.3, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
            SceneObject("wall_right", "灰色の壁（右）", (2.325, -1.2), (1.65, 0.3, 0.5), (0.5, 0.5, 0.5), is_obstacle=True),
        ),
        camera_pos=(-1.5, -5.5, 6.0),
        camera_lookat=(2.3, 0.0, 0.0),
    ),
    "danger": SceneSpec(
        name="danger",
        description="ゴールの赤い箱と、その手前に置かれた紫の箱（危険物）がある部屋",
        objects=(
            SceneObject("red_box", "赤い箱（ゴール）", (4.5, 0.0), BOX, (0.9, 0.1, 0.1)),
            SceneObject("purple_box", "紫の箱（危険物）", (2.0, 0.3), BOX, (0.6, 0.2, 0.8)),
        ),
        camera_pos=(-1.5, -5.5, 5.5),
        camera_lookat=(2.3, 0.0, 0.0),
    ),
}
