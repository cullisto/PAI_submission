import argparse
import os
import pickle
import torch
from go2_env import Go2Env
from rsl_rl.runners import OnPolicyRunner
import genesis as gs

# メイン
def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="go2-walking")
    parser.add_argument("--ckpt", type=int, default=100)
    args = parser.parse_args()

    # CUDAが使えればGPU、使えなければ（ローカルPCなど）CPUで実行
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # Genesisの初期化
    gs.init(backend=gs.gpu if device.startswith("cuda") else gs.cpu)

    # 各種設定の取得
    # go2_train.py と同じく、スクリプトと同じフォルダの logs/ から読み込む
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", args.exp_name)
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(open(os.path.join(log_dir, "cfgs.pkl"), "rb"))
    reward_cfg["reward_scales"] = {}

    # 環境の初期化
    env = Go2Env(
        num_envs=1,  # 環境数を指定
        env_cfg=env_cfg,  # 環境設定
        obs_cfg=obs_cfg,  # 観測設定
        reward_cfg=reward_cfg,  # 報酬設定
        command_cfg=command_cfg,  # 命令設定
        show_viewer=True,  # ビューアを表示するかどうか
        device=device,
    )

    # OnPolicyRunnerの初期化
    runner = OnPolicyRunner(env, train_cfg, log_dir, device=device)

    # モデルの読み込み
    # Colab(GPU)で保存したモデルをCPUでも読めるよう、map_locationを指定して読み込む
    # (rsl_rl v1.0.2 の runner.load() は map_location を指定できないため)
    resume_path = os.path.join(log_dir, f"model_{args.ckpt}.pt")
    loaded_dict = torch.load(resume_path, map_location=device)
    runner.alg.actor_critic.load_state_dict(loaded_dict["model_state_dict"])
    policy = runner.get_inference_policy(device=device)

    # 環境のリセット
    obs, _ = env.reset()

    # 推論ループ
    with torch.no_grad():
        while True:
            actions = policy(obs)  # ポリシーで行動を計算
            obs, _, rews, dones, infos = env.step(actions)  # 環境を1ステップ進行


if __name__ == "__main__":
    main()
