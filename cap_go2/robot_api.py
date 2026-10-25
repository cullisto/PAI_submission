"""Go2 を Code as Policies で動かすためのロボット API.

構成:
  - Go2Robot : Genesis のシミュレーション（Go2Env）と学習済み歩行方策（rsl_rl）をまとめたもの。
               速度指令 (vx, vy, yaw_rate) を与えると、方策が関節を動かして歩く。
  - RobotAPI : LLM が生成するコードから呼べる関数群。ここの docstring がそのままプロンプトの API 説明になる。

LLM が書いたコードは RobotAPI のメソッドだけを使ってロボットを動かす（下位の歩行制御は強化学習の方策が担当）。
"""

import functools
import inspect
import math
import os
import pickle
import sys
from pathlib import Path

import torch

import genesis as gs

ROOT = Path(__file__).resolve().parents[1]
SRC_EXT = ROOT / "src_ext"
sys.path.insert(0, str(SRC_EXT))

from go2_env import Go2Env  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from scenes import SceneSpec  # noqa: E402

CONTROL_DT = 0.02  # 方策の制御周期 [s]（Go2Env.dt と同じ）

# 学習時の速度指令の範囲（go2_train.py の command_cfg と合わせる）。これを超える指令は範囲内に丸める
VX_RANGE = (-0.5, 1.0)
VY_RANGE = (-0.5, 0.5)
YAW_RATE_RANGE = (-1.0, 1.0)


class RobotFallenError(RuntimeError):
    """ロボットが転倒した."""


class SimTimeLimitError(RuntimeError):
    """生成コードの実行がシミュレーション時間の上限を超えた."""


def wrap_angle(rad):
    """角度を [-pi, pi) に正規化する."""
    return (rad + math.pi) % (2.0 * math.pi) - math.pi


def clip(value, low, high):
    return max(low, min(high, value))


def default_exp_name():
    """全方向歩行の方策 (go2-omni) があればそれを、なければ前進のみの方策 (go2-walking) を使う."""
    for name in ("go2-omni", "go2-walking"):
        if (SRC_EXT / "logs" / name / "cfgs.pkl").exists():
            return name
    raise FileNotFoundError(f"学習済みモデルが見つかりません: {SRC_EXT / 'logs'}")


def latest_checkpoint(log_dir):
    ckpts = sorted(log_dir.glob("model_*.pt"), key=lambda p: int(p.stem.split("_")[1]))
    if not ckpts:
        raise FileNotFoundError(f"model_*.pt が見つかりません: {log_dir}")
    return ckpts[-1]


class Go2Robot:
    """Genesis 上の Go2 と学習済み歩行方策."""

    def __init__(self, scene_spec: SceneSpec, exp_name=None, ckpt=None, show_viewer=False, video_path=None,
                 video_fps=25, max_sim_time=120.0):
        self.scene_spec = scene_spec
        self.max_sim_time = max_sim_time
        self.video_path = video_path
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if not gs._initialized:
            gs.init(backend=gs.gpu if self.device.startswith("cuda") else gs.cpu, logging_level="warning")

        # 学習時の設定を読み込み、CaP 実行用に一部を上書きする
        self.exp_name = exp_name or default_exp_name()
        log_dir = SRC_EXT / "logs" / self.exp_name
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(open(log_dir / "cfgs.pkl", "rb"))
        reward_cfg["reward_scales"] = {}
        # 生成コードの実行中に、エピソード終了による自動リセットや速度指令の自動再サンプリングが起きないようにする
        env_cfg["episode_length_s"] = 1e6
        env_cfg["resampling_time_s"] = 1e6
        x0, y0 = scene_spec.robot_start
        yaw0 = math.radians(scene_spec.robot_start_yaw_deg)
        env_cfg["base_init_pos"] = [x0, y0, 0.42]
        env_cfg["base_init_quat"] = [math.cos(yaw0 / 2), 0.0, 0.0, math.sin(yaw0 / 2)]  # (w, x, y, z)
        # 学習時と違う命令範囲を使っていないか確認するため保持
        self.trained_command_cfg = command_cfg

        self.camera = None
        self.env = Go2Env(
            num_envs=1,
            env_cfg=env_cfg,
            obs_cfg=obs_cfg,
            reward_cfg=reward_cfg,
            command_cfg=command_cfg,
            show_viewer=show_viewer,
            device=self.device,
            scene_setup=self._setup_scene,
        )

        # 学習済み方策の読み込み（GPU で保存したモデルも CPU で読めるよう map_location を指定）
        runner = OnPolicyRunner(self.env, train_cfg, str(log_dir), device=self.device)
        self.ckpt_path = log_dir / f"model_{ckpt}.pt" if ckpt is not None else latest_checkpoint(log_dir)
        loaded = torch.load(self.ckpt_path, map_location=self.device)
        runner.alg.actor_critic.load_state_dict(loaded["model_state_dict"])
        self.policy = runner.get_inference_policy(device=self.device)

        self.obs, _ = self.env.reset()
        self.env.commands[:] = 0.0
        self.sim_time = 0.0
        self.code_start_time = None  # 生成コードの実行開始時刻（これ以前は着地待ち）
        self.current_call = "(setup)"
        self.trajectory = []  # 各制御ステップの状態
        self.events = []  # API 呼び出しの記録（レポート用）

        if video_path is not None:
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            self.camera.start_recording(save_to_filename=str(video_path), fps=video_fps)

        # 生成された直後は空中にいるので、着地して静止するまで待つ
        self.run_command(0.0, 0.0, 0.0, 1.0)

    def _setup_scene(self, scene):
        """箱と録画用カメラをシーンに追加する（Go2Env のビルド前に呼ばれる）."""
        for obj in self.scene_spec.objects:
            scene.add_entity(
                gs.morphs.Box(pos=(obj.pos[0], obj.pos[1], obj.size[2] / 2), size=obj.size, fixed=True),
                surface=gs.surfaces.Default(color=obj.color),
            )
        if self.video_path is not None:
            self.camera = scene.add_camera(
                res=(960, 540),
                pos=self.scene_spec.camera_pos,
                lookat=self.scene_spec.camera_lookat,
                fov=45,
                GUI=False,
            )

    # ---- 状態 ----
    @property
    def position(self):
        pos = self.env.base_pos[0]
        return float(pos[0]), float(pos[1])

    @property
    def yaw(self):
        """ワールド座標での向き [rad]（x 軸から左回りが正）."""
        w, x, y, z = (float(v) for v in self.env.base_quat[0])
        return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))

    def _roll_pitch(self):
        w, x, y, z = (float(v) for v in self.env.base_quat[0])
        roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
        pitch = math.asin(clip(2.0 * (w * y - z * x), -1.0, 1.0))
        return roll, pitch

    # ---- 制御 ----
    def run_command(self, vx, vy, yaw_rate, duration):
        """速度指令を duration 秒間与え続ける（制御周期ごとに方策を実行）."""
        n_steps = max(1, round(duration / CONTROL_DT))
        cmd = torch.tensor([vx, vy, yaw_rate], device=self.device, dtype=gs.tc_float)
        for _ in range(n_steps):
            self.env.commands[:] = cmd
            with torch.no_grad():
                actions = self.policy(self.obs)
            self.obs, _, _, _, _ = self.env.step(actions)
            self.sim_time += CONTROL_DT
            self._record(vx, vy, yaw_rate)
            self._check_safety()

    def _record(self, vx, vy, yaw_rate):
        x, y = self.position
        self.trajectory.append({
            "t": round(self.sim_time, 3),
            "x": x,
            "y": y,
            "z": float(self.env.base_pos[0, 2]),
            "yaw_deg": math.degrees(self.yaw),
            "cmd_vx": vx,
            "cmd_vy": vy,
            "cmd_yaw_rate": yaw_rate,
            "api_call": self.current_call,
        })

    def _check_safety(self):
        roll, pitch = self._roll_pitch()
        if float(self.env.base_pos[0, 2]) < 0.15 or abs(roll) > 1.0 or abs(pitch) > 1.0:
            raise RobotFallenError(f"ロボットが転倒しました（t={self.sim_time:.1f}s, 位置={self.position}）")
        if self.code_start_time is not None and self.sim_time - self.code_start_time > self.max_sim_time:
            raise SimTimeLimitError(f"シミュレーション時間の上限 {self.max_sim_time:.0f} 秒を超えました")

    def log_event(self, text):
        self.events.append(f"[t={self.sim_time:6.2f}s] {text}")

    def close(self):
        if self.camera is not None and self.video_path is not None:
            self.camera.stop_recording()


def api_function(func):
    """RobotAPI の公開関数に付ける。呼び出しを記録し、軌跡にどの関数の実行中かを残す."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        call = f"{func.__name__}({', '.join([repr(a) for a in args] + [f'{k}={v!r}' for k, v in kwargs.items()])})"
        outer_call = self.robot.current_call
        is_top_level = outer_call == "(code)"
        if is_top_level:
            self.robot.current_call = call
        result = func(self, *args, **kwargs)
        if is_top_level:
            self.robot.current_call = outer_call
            self.robot.log_event(f"{call} -> {result!r}" if result is not None else call)
        return result

    wrapper.is_api_function = True
    return wrapper


class RobotAPI:
    """LLM が生成するコードから呼べる関数群.

    座標系: ワールド座標 [m]。向き(yaw) は x 軸から反時計回り（左回り）が正の角度 [deg]。
    「前・後ろ・左・右」はロボット自身から見た方向。
    """

    def __init__(self, robot: Go2Robot):
        self.robot = robot

    # ---------------- 低レベル: 速度指令 ----------------
    @api_function
    def walk(self, vx: float, vy: float = 0.0, yaw_rate: float = 0.0, duration: float = 1.0) -> None:
        """速度指令を与えて duration 秒間歩く（ロボット自身から見た向きで指定）.

        vx: 前後の速度 [m/s]（前が正）。範囲 -0.5〜1.0
        vy: 左右の速度 [m/s]（左が正）。範囲 -0.5〜0.5
        yaw_rate: 旋回の角速度 [rad/s]（左回りが正）。範囲 -1.0〜1.0
        範囲外の値は範囲内に丸められる。
        """
        clipped = (clip(vx, *VX_RANGE), clip(vy, *VY_RANGE), clip(yaw_rate, *YAW_RATE_RANGE))
        if clipped != (vx, vy, yaw_rate):
            self.robot.log_event(f"速度指令を範囲内に丸めました: {(vx, vy, yaw_rate)} -> {clipped}")
        self.robot.run_command(*clipped, duration)

    @api_function
    def stop(self, duration: float = 1.0) -> None:
        """その場で duration 秒間静止する."""
        self.robot.run_command(0.0, 0.0, 0.0, duration)

    # ---------------- 高レベル: 移動・旋回 ----------------
    @api_function
    def move_forward(self, distance: float) -> None:
        """今の向きのまま distance [m] だけ前進する（負の値なら後退）."""
        self._move_body(distance, 0.0)

    @api_function
    def move_sideways(self, distance: float) -> None:
        """今の向きのまま distance [m] だけ横に移動する（左が正、右が負）."""
        self._move_body(0.0, distance)

    @api_function
    def turn(self, angle_deg: float) -> None:
        """その場で angle_deg [deg] だけ旋回する（左回りが正、右回りが負）."""
        self._turn_to(self.robot.yaw + math.radians(angle_deg), timeout=abs(angle_deg) / 30.0 + 5.0)

    @api_function
    def turn_to(self, yaw_deg: float) -> None:
        """その場で旋回して、ワールド座標での向きを yaw_deg [deg] にする."""
        self._turn_to(math.radians(yaw_deg), timeout=15.0)

    @api_function
    def face(self, x: float, y: float) -> None:
        """その場で旋回して、点 (x, y) の方を向く."""
        px, py = self.robot.position
        self._turn_to(math.atan2(y - py, x - px), timeout=15.0)

    @api_function
    def move_to(self, x: float, y: float, tolerance: float = 0.3, timeout: float = 30.0) -> bool:
        """点 (x, y) に向かって歩く（向きを変えながら直進する。障害物は避けない）.

        tolerance: 到着とみなす距離 [m]
        timeout: これを超えたら諦める時間 [s]
        到着したら True、時間切れなら False を返す。
        """
        t_start = self.robot.sim_time
        while True:
            px, py = self.robot.position
            dx, dy = x - px, y - py
            dist = math.hypot(dx, dy)
            if dist <= tolerance:
                self.robot.run_command(0.0, 0.0, 0.0, 0.3)
                return True
            if self.robot.sim_time - t_start > timeout:
                self.robot.run_command(0.0, 0.0, 0.0, 0.3)
                return False
            heading_err = wrap_angle(math.atan2(dy, dx) - self.robot.yaw)
            yaw_rate = clip(2.0 * heading_err, *YAW_RATE_RANGE)
            vx = clip(1.2 * dist, 0.15, 0.8) * max(0.0, math.cos(heading_err)) ** 2
            self.robot.run_command(vx, 0.0, yaw_rate, 0.1)

    # ---------------- 認識 ----------------
    @api_function
    def get_position(self) -> tuple:
        """ロボットの現在位置 (x, y) [m] を返す."""
        x, y = self.robot.position
        return round(x, 3), round(y, 3)

    @api_function
    def get_yaw(self) -> float:
        """ロボットの現在の向き [deg] を返す（x 軸から左回りが正、-180〜180）."""
        return round(math.degrees(self.robot.yaw), 1)

    @api_function
    def get_objects(self) -> list:
        """シーン内の物体の一覧を返す.

        各要素は dict: {"name", "description", "x", "y", "size_x", "size_y", "is_obstacle"}
        (x, y) は物体の中心、size_x / size_y は x / y 方向の大きさ [m]。
        """
        return [
            {
                "name": o.name,
                "description": o.description,
                "x": o.pos[0],
                "y": o.pos[1],
                "size_x": o.size[0],
                "size_y": o.size[1],
                "is_obstacle": o.is_obstacle,
            }
            for o in self.robot.scene_spec.objects
        ]

    @api_function
    def get_object_position(self, name: str) -> tuple:
        """名前が name の物体の中心位置 (x, y) [m] を返す。存在しない名前なら ValueError."""
        for o in self.robot.scene_spec.objects:
            if o.name == name:
                return o.pos
        raise ValueError(f"物体 '{name}' は存在しません。候補: {[o.name for o in self.robot.scene_spec.objects]}")

    @api_function
    def distance_to(self, x: float, y: float) -> float:
        """ロボットから点 (x, y) までの距離 [m] を返す."""
        px, py = self.robot.position
        return round(math.hypot(x - px, y - py), 3)

    # ---------------- 内部処理（LLM には見せない） ----------------
    def _turn_to(self, target_yaw, timeout):
        t_start = self.robot.sim_time
        while self.robot.sim_time - t_start < timeout:
            err = wrap_angle(target_yaw - self.robot.yaw)
            if abs(err) < math.radians(3.0):
                break
            yaw_rate = clip(2.5 * err, *YAW_RATE_RANGE)
            if abs(yaw_rate) < 0.3:
                yaw_rate = math.copysign(0.3, yaw_rate)
            self.robot.run_command(0.0, 0.0, yaw_rate, 0.1)
        self.robot.run_command(0.0, 0.0, 0.0, 0.3)

    def _move_body(self, forward, left):
        """向きを保ったまま、ロボット座標で (forward, left) [m] だけ移動する."""
        heading = self.robot.yaw
        px, py = self.robot.position
        tx = px + forward * math.cos(heading) - left * math.sin(heading)
        ty = py + forward * math.sin(heading) + left * math.cos(heading)
        timeout = math.hypot(forward, left) / 0.2 + 5.0
        t_start = self.robot.sim_time
        while self.robot.sim_time - t_start < timeout:
            px, py = self.robot.position
            ex, ey = tx - px, ty - py
            if math.hypot(ex, ey) < 0.1:
                break
            yaw = self.robot.yaw
            along = ex * math.cos(yaw) + ey * math.sin(yaw)
            lateral = -ex * math.sin(yaw) + ey * math.cos(yaw)
            vx = clip(1.5 * along, VX_RANGE[0], 0.8)
            vy = clip(1.5 * lateral, -0.4, 0.4)
            yaw_rate = clip(2.0 * wrap_angle(heading - yaw), *YAW_RATE_RANGE)
            self.robot.run_command(vx, vy, yaw_rate, 0.1)
        self.robot.run_command(0.0, 0.0, 0.0, 0.3)


# API の抽象度レベル（CaP-X のように、LLM に渡す API の粒度を変えて比較できるようにする）
API_LEVELS = {
    # 速度指令と認識だけ: LLM が自分で閉ループ制御を書く必要がある
    "low": ["walk", "stop", "get_position", "get_yaw", "get_objects", "get_object_position", "distance_to"],
    # 移動・旋回の高レベル関数も使える
    "high": [
        "walk", "stop", "move_forward", "move_sideways", "turn", "turn_to", "face", "move_to",
        "get_position", "get_yaw", "get_objects", "get_object_position", "distance_to",
    ],
}


def api_reference(level):
    """プロンプトに載せる API 説明を、RobotAPI の型注釈と docstring から作る."""
    lines = []
    for name in API_LEVELS[level]:
        func = getattr(RobotAPI, name)
        sig = inspect.signature(func)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        sig_str = f"{name}({', '.join(str(p) for p in params)})"
        if sig.return_annotation is not inspect.Signature.empty:
            ret = sig.return_annotation
            sig_str += f" -> {ret.__name__ if isinstance(ret, type) else ret}"
        doc = inspect.getdoc(func) or ""
        lines.append(f"- `{sig_str}`\n" + "\n".join(f"    {line}" if line else "" for line in doc.splitlines()))
    return "\n".join(lines)
