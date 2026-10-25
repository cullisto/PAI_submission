"""オープンウェイトの LLM（例: Qwen の 4B モデル）で Code as Policies の評価を自動で回す.

流れ（1 エピソード = 1 タスク × 1 API レベル × 1 サンプル）:
    プロンプト生成 → LLM が応答を生成 → cap_run.py で実行・判定（別プロセス）
    → 失敗したら修正依頼を会話に追加して LLM に再生成させる（最大 --max-attempts 回）

LLM の呼び出し方（--backend）:
    hf     : Hugging Face transformers で同じプロセス内に読み込む（Colab の GPU 向け）
    openai : OpenAI 互換の API サーバー（Ollama, vLLM, llama.cpp server など）に送る
    mock   : 決まった応答を返す（動作確認用。LLM は使わない）

例:
    # Colab（T4 GPU）
    python cap_auto.py --backend hf --model Qwen/Qwen3-4B-Instruct-2507 --samples 3
    # 手元の Ollama
    python cap_auto.py --backend openai --base-url http://localhost:11434/v1 --model qwen3:4b --samples 1 --tasks T01 H03

途中で止まっても、同じコマンドをもう一度実行すれば終わっていないエピソードから再開する（auto_progress_<名前>.jsonl）。
集計は cap_summary.py で行う。
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# 生成のたびに長さの違うテンソルを確保し直すことによる GPU メモリの断片化を減らす（torch の読み込み前に設定する）
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

from cap_common import (
    CAP_DIR, PROMPT_VERSION, RESULTS_FIELDS, build_prompt, extract_code, new_run_dir, save_json, strip_thinking,
)
from scenes import SCENES
from tasks import TASKS

# モデル提供元が推奨しているサンプリング設定（Qwen3 系の推奨値。--temperature などで上書きできる）
SAMPLING_DEFAULTS = {
    # 思考なし。正常な応答は数百トークンなので、上限に達するのは同じ文を繰り返して止まらなくなったときだけ。
    # 上限を下げて、そのときの生成時間と会話の履歴の膨張を抑える
    False: {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "max_new_tokens": 2048},
    True: {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "max_new_tokens": 8192},  # 思考あり
}
PREFILL_CHUNK = 512  # 入力をモデルに通すときの分割の長さ（トークン）


# ---------------- LLM の呼び出し ----------------
class HFChat:
    """transformers でモデルを読み込んで生成する."""

    def __init__(self, model_id, thinking, sampling):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.thinking = thinking
        self.sampling = sampling
        if torch.cuda.is_available():
            # bfloat16 はハードウェアで対応している GPU（compute capability 8.0 以上: A100, L4 など）だけで使う。
            # T4（7.5）では is_bf16_supported() が True でも内部でエミュレーションになり、注意機構の省メモリな計算が
            # 使えず、入力の長さの 2 乗のメモリを確保して GPU のメモリが足りなくなる
            major, _ = torch.cuda.get_device_capability()
            dtype = torch.bfloat16 if major >= 8 else torch.float16
        else:
            dtype = torch.float32
        self.dtype_name = str(dtype).replace("torch.", "")
        print(f"モデルを読み込み中: {model_id}（{dtype}）", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # transformers 4.56 以降は dtype（それより前は torch_dtype）
        self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype, device_map="auto")
        # 応答の記録から取り除く特殊トークン（<think> と </think> は思考の区切りとして残す）
        self.strip_tokens = [t for t in self.tokenizer.all_special_tokens if t not in ("<think>", "</think>")]

    def prefill(self, input_ids):
        """入力を PREFILL_CHUNK トークンずつモデルに通して、KV キャッシュを作る（最後の 1 トークンは generate に任せる）.

        入力をまとめて通すと、注意機構の省メモリな計算が使えない環境（T4 など）では「ヘッド数 × 入力長 × 入力長」の
        行列を確保する（6533 トークンで約 5 GB）。分けて通せば「ヘッド数 × 分割の長さ × 入力長」で済む。
        出力は変わらない（同じキャッシュを一度に作るか、分けて作るかの違いだけ）。
        """
        from transformers import DynamicCache

        cache = DynamicCache()
        decoder = self.model.get_decoder()  # 語彙数 × 入力長のロジットを計算しないよう、出力層の手前まで通す
        n = input_ids.shape[1] - 1
        for start in range(0, n, PREFILL_CHUNK):
            decoder(input_ids=input_ids[:, start:min(start + PREFILL_CHUNK, n)], past_key_values=cache, use_cache=True)
        return cache

    def chat(self, messages, seed):
        torch = self.torch
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=self.thinking
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        prompt_tokens = int(inputs["input_ids"].shape[1])
        s = self.sampling
        on_gpu = torch.cuda.is_available()
        if on_gpu:
            torch.cuda.reset_peak_memory_stats()
        for retry in range(2):
            # やり直したときも同じ乱数で生成されるよう、毎回シードを設定する
            torch.manual_seed(seed)
            try:
                with torch.no_grad():
                    cache = self.prefill(inputs["input_ids"])
                    output = self.model.generate(
                        **inputs,
                        past_key_values=cache,
                        max_new_tokens=s["max_new_tokens"],
                        do_sample=s["temperature"] > 0,
                        temperature=s["temperature"],
                        top_p=s["top_p"],
                        top_k=s["top_k"],
                    )
                break
            except torch.cuda.OutOfMemoryError:
                # キャッシュを解放して 1 回だけやり直す。それでも足りなければ止める（途中から再開できる）
                cache = None
                torch.cuda.empty_cache()
                if retry == 1:
                    raise
                print(f"    GPU メモリ不足のため、キャッシュを解放して生成をやり直します（入力 {prompt_tokens} トークン）", flush=True)
        generated = output[0][prompt_tokens:].tolist()
        response = self.tokenizer.decode(generated, skip_special_tokens=False)
        for token in self.strip_tokens:
            response = response.replace(token, "")
        usage = {"prompt_tokens": prompt_tokens, "completion_tokens": len(generated), "dtype": self.dtype_name}
        if on_gpu:
            usage["peak_gpu_memory_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
            # 生成に使ったテンソルを手放し、次の生成やシミュレーションのためにメモリを空ける
            del output, inputs, cache
            torch.cuda.empty_cache()
        return response.strip(), usage


class OpenAIChat:
    """OpenAI 互換の /chat/completions に送る（Ollama, vLLM, llama.cpp server など）."""

    def __init__(self, base_url, model, sampling, api_key=None):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.sampling = sampling
        self.api_key = api_key

    def chat(self, messages, seed):
        s = self.sampling
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": s["temperature"],
            "top_p": s["top_p"],
            "max_tokens": s["max_new_tokens"],
            "seed": seed,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(request, timeout=3600) as res:
            data = json.loads(res.read().decode("utf-8"))
        message = data["choices"][0]["message"]
        response = message.get("content") or ""
        # サーバーによっては思考過程を別の欄で返すので、記録用に <think> で包んで残す
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        if reasoning:
            response = f"<think>\n{reasoning}\n</think>\n{response}"
        usage = data.get("usage", {})
        return response.strip(), {"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")}


class MockChat:
    """動作確認用: 1 回目はわざと失敗するコード、2 回目以降は止まるだけのコードを返す."""

    def chat(self, messages, seed):
        if len(messages) == 1:
            return "```python\nget_object_position('no_such_box')\n```", {"prompt_tokens": 0, "completion_tokens": 0}
        return "修正します。\n```python\nstop(0.5)\n```", {"prompt_tokens": 0, "completion_tokens": 0}


# ---------------- 評価の進捗（再開用） ----------------
def load_progress(path):
    if not path.exists():
        return {}
    done = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            done[(record["task_id"], record["api_level"], record["sample"])] = record
    return done


def drop_environment_errors(progress_path, done):
    """実行環境エラー（シミュレーションのプロセスの異常終了など）で終わったエピソードを、未完了に戻す.

    LLM の生成したコードの良し悪しとは関係がないので、評価に含めずにやり直す。
    進捗ファイルから該当する記録を除き（元のファイルは _before_cleanup として残す）、残りの記録を返す。
    """
    errored = {key: r for key, r in done.items() if any(a["failure_type"] == "実行環境エラー" for a in r["attempts"])}
    if not errored:
        return done
    shutil.copy(progress_path, progress_path.with_name(progress_path.stem + "_before_cleanup.jsonl"))
    kept = {key: r for key, r in done.items() if key not in errored}
    progress_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept.values()), encoding="utf-8")
    print(f"実行環境エラーで終わったエピソード {len(errored)} 件をやり直します: "
          f"{', '.join(f'{t}/{lv}/s{s}' for t, lv, s in sorted(errored))}", flush=True)
    return kept


def set_aside_incomplete_runs(runs_base, done, results_csv):
    """途中で止まったエピソード（進捗に記録されていない実行記録）を退避し、その結果の行を CSV から除く.

    エピソードは最後まで終わってから進捗に記録されるため、途中で止まったエピソードは再開時に最初からやり直す。
    やり直す前の中途半端な記録が集計に混ざらないよう、runs_auto/<名前>/_incomplete/ に移す。
    """
    if not runs_base.exists():
        return
    finished = {record["run_id"] for record in done.values()}
    incomplete = [p for p in runs_base.iterdir() if p.is_dir() and not p.name.startswith("_") and p.name not in finished]
    if not incomplete:
        return
    aside_dir = runs_base / "_incomplete"
    aside_dir.mkdir(exist_ok=True)
    for run_dir in incomplete:
        shutil.move(str(run_dir), str(aside_dir / run_dir.name))
    names = {p.name for p in incomplete}
    if results_csv.exists():
        with open(results_csv, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        kept = [row for row in rows if row["run_id"] not in names]
        if len(kept) != len(rows):
            shutil.copy(results_csv, results_csv.with_name(results_csv.stem + "_before_cleanup.csv"))
            with open(results_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=RESULTS_FIELDS)
                writer.writeheader()
                writer.writerows(kept)
    print(f"途中で止まったエピソード {len(incomplete)} 件を {aside_dir} に退避し、結果の行を除きました: "
          f"{', '.join(sorted(names))}", flush=True)


def append_progress(path, record):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


HISTORY_MAX_CHARS = 2000  # 途中で切れた応答などを会話の履歴に残すときの最大文字数


def history_content(response, is_truncated):
    """修正を依頼するときに、会話の履歴に入れる LLM の応答.

    思考過程は含めない（Qwen3 の推奨）。出力が上限で途中で切れた場合やコードを取り出せなかった場合は、
    同じ文の繰り返しなどで長くなっていることが多く、そのまま入れると次の入力が膨らむので先頭だけ残す。
    """
    text = strip_thinking(response).strip()
    if (is_truncated or extract_code(response) is None) and len(text) > HISTORY_MAX_CHARS:
        return text[:HISTORY_MAX_CHARS] + "\n…（出力が長すぎるため、ここから先は省略）"
    return text


# ---------------- 1 エピソード ----------------
def run_episode(llm, args, task_id, api_level, sample, model_label, results_csv, runs_base):
    task = TASKS[task_id]
    run_dir = new_run_dir(f"{task_id}_{api_level}_s{sample}", base_dir=runs_base)
    prompt = build_prompt(SCENES[task.scene], task.instruction, api_level)
    (run_dir / "attempt_1" / "prompt.md").write_text(prompt, encoding="utf-8")
    save_json(run_dir / "meta.json", {
        "run_id": run_dir.name,
        "task_id": task_id,
        "instruction": task.instruction,
        "scene": task.scene,
        "api_level": api_level,
        "model": model_label,
        "prompt_version": PROMPT_VERSION,
        "sample": sample,
        "backend": args.backend,
        "sampling": llm_sampling(args),
    })

    messages = [{"role": "user", "content": prompt}]
    attempts = []
    for attempt in range(1, args.max_attempts + 1):
        attempt_dir = run_dir / f"attempt_{attempt}"
        seed = args.seed + 1000 * sample + attempt
        t0 = time.time()
        response, usage = llm.chat(messages, seed)
        gen_time = time.time() - t0
        response_path = attempt_dir / "response.md"
        response_path.write_text(response, encoding="utf-8")
        is_truncated = usage.get("completion_tokens") is not None and usage["completion_tokens"] >= llm_sampling(args)["max_new_tokens"]
        save_json(attempt_dir / "generation.json", {**usage, "seconds": round(gen_time, 1), "seed": seed,
                                                    "is_truncated": is_truncated})

        cmd = [sys.executable, str(CAP_DIR / "cap_run.py"), str(run_dir), "--response", str(response_path),
               "--results", str(results_csv), "--max-attempts", str(args.max_attempts), "--no-clipboard"]
        if not args.video:
            cmd.append("--no-video")
        if args.exp:
            cmd += ["--exp", args.exp]
        t1 = time.time()
        env = {**os.environ, "PYTHONUTF8": "1"}
        if args.sim_device == "cpu":
            # GPU を隠すと Go2Robot は CPU で動く。GPU のメモリは LLM だけが使う
            env["CUDA_VISIBLE_DEVICES"] = ""
        proc = subprocess.run(cmd, cwd=CAP_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=env, timeout=args.sim_timeout)
        (attempt_dir / "cap_run_output.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
        result_path = attempt_dir / "result.json"
        if not result_path.exists():
            # シミュレーション側が異常終了した（生成コードの問題ではないので評価から除外できるよう区別する）
            attempts.append({"attempt": attempt, "success": False, "failure_type": "実行環境エラー",
                             "gen_seconds": round(gen_time, 1), "sim_seconds": round(time.time() - t1, 1)})
            print(f"    試行{attempt}: 実行環境エラー（{attempt_dir / 'cap_run_output.log'} を確認）", flush=True)
            break
        result = json.loads(result_path.read_text(encoding="utf-8"))
        attempts.append({"attempt": attempt, "success": bool(result["success"]), "failure_type": result["failure_type"],
                         "completion_tokens": usage.get("completion_tokens"), "is_truncated": is_truncated,
                         "gen_seconds": round(gen_time, 1), "sim_seconds": round(time.time() - t1, 1)})
        gpu_text = f", GPU 最大 {usage['peak_gpu_memory_gb']} GB" if "peak_gpu_memory_gb" in usage else ""
        print(f"    試行{attempt}: {'成功' if result['success'] else '失敗（' + result['failure_type'] + '）'}"
              f"  生成 {gen_time:.0f}s / {usage.get('completion_tokens')} tokens{gpu_text}, 実行 {time.time() - t1:.0f}s",
              flush=True)
        if result["success"]:
            break
        feedback_path = run_dir / f"attempt_{attempt + 1}" / "prompt.md"
        if not feedback_path.exists():
            break
        messages += [{"role": "assistant", "content": history_content(response, is_truncated)},
                     {"role": "user", "content": feedback_path.read_text(encoding="utf-8")}]

    return {
        "task_id": task_id,
        "api_level": api_level,
        "sample": sample,
        "run_id": run_dir.name,
        "model": model_label,
        "success_first": attempts[0]["success"],
        "success_final": attempts[-1]["success"],
        "n_attempts": len(attempts),
        "attempts": attempts,
    }


def llm_sampling(args):
    sampling = dict(SAMPLING_DEFAULTS[args.thinking])
    for key in sampling:
        value = getattr(args, key)
        if value is not None:
            sampling[key] = value
    return sampling


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", choices=["hf", "openai", "mock"], required=True)
    parser.add_argument("--model", default="mock", help="モデル名（hf なら Hugging Face のモデル ID）")
    parser.add_argument("--base-url", default="http://localhost:11434/v1", help="openai バックエンドの URL")
    parser.add_argument("--label", default=None, help="結果に記録するモデル名（省略時は自動）")
    parser.add_argument("--tasks", nargs="+", default=["all"], help="タスク ID（all / basic=T01〜T11 / hard=H01〜H07 も可）")
    parser.add_argument("--api-levels", nargs="+", default=["high", "low"], choices=["high", "low"])
    parser.add_argument("--samples", type=int, default=3, help="各タスク・API レベルで何回サンプリングするか")
    parser.add_argument("--max-attempts", type=int, default=3, help="1 エピソードの最大試行回数（修正を含む）")
    parser.add_argument("--thinking", action="store_true", help="思考モードを使う（対応モデルのみ。生成が長くなる）")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", dest="top_p", type=float, default=None)
    parser.add_argument("--top-k", dest="top_k", type=int, default=None)
    parser.add_argument("--max-new-tokens", dest="max_new_tokens", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--video", action="store_true", help="動画を録画する（遅くなる。Colab では描画できないことがある）")
    parser.add_argument("--exp", default=None, help="使う学習済み方策（省略時は go2-omni）")
    parser.add_argument("--sim-timeout", type=int, default=1800, help="1 試行の実行の制限時間 [s]")
    parser.add_argument("--sim-device", choices=["cpu", "gpu"], default="cpu",
                        help="シミュレーションを動かす装置（既定は cpu。GPU のメモリを LLM に空けておくため）")
    parser.add_argument("--out-dir", default=str(CAP_DIR), help="結果・進捗・実行記録（runs_auto/）の保存先")
    args = parser.parse_args()

    if args.tasks == ["all"]:
        task_ids = list(TASKS)
    elif args.tasks == ["basic"]:
        task_ids = [t for t in TASKS if t.startswith("T")]
    elif args.tasks == ["hard"]:
        task_ids = [t for t in TASKS if t.startswith("H")]
    else:
        task_ids = args.tasks
    unknown = [t for t in task_ids if t not in TASKS]
    if unknown:
        parser.error(f"不明なタスク: {unknown}")

    slug = re.sub(r"[^A-Za-z0-9]+", "-", args.model).strip("-").lower() + ("-think" if args.thinking else "")
    # プロンプトの版ごとに結果・進捗・実行記録を分ける
    slug += f"_{PROMPT_VERSION}"
    label = args.label or f"{args.model}{' (thinking)' if args.thinking else ''}"
    out_dir = Path(args.out_dir)
    results_csv = out_dir / f"results_{slug}.csv"
    progress_path = out_dir / f"auto_progress_{slug}.jsonl"
    # 手動実行の runs/ と分ける（cap_run.py は引数なしだと runs/ の最新を使うため、混ざると取り違える）
    runs_base = out_dir / "runs_auto" / slug
    done = drop_environment_errors(progress_path, load_progress(progress_path))
    # やり直すエピソードと途中で止まったエピソードの記録は、退避して集計から外す
    set_aside_incomplete_runs(runs_base, done, results_csv)

    episodes = [(t, lv, s) for s in range(args.samples) for lv in args.api_levels for t in task_ids]
    todo = [e for e in episodes if e not in done]
    print(f"モデル: {label} / バックエンド: {args.backend} / サンプリング: {llm_sampling(args)}")
    print(f"シミュレーション: {args.sim_device}")
    print(f"エピソード: 全 {len(episodes)}、完了済み {len(episodes) - len(todo)}、残り {len(todo)}")
    print(f"結果: {results_csv.name}, 進捗: {progress_path.name}", flush=True)
    if not todo:
        return

    if args.backend == "hf":
        llm = HFChat(args.model, args.thinking, llm_sampling(args))
    elif args.backend == "openai":
        llm = OpenAIChat(args.base_url, args.model, llm_sampling(args), api_key=os.environ.get("OPENAI_API_KEY"))
    else:
        llm = MockChat()

    for i, (task_id, api_level, sample) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {task_id} / {api_level} / サンプル {sample}", flush=True)
        record = run_episode(llm, args, task_id, api_level, sample, label, results_csv, runs_base)
        append_progress(progress_path, record)

    records = load_progress(progress_path).values()
    for level in args.api_levels:
        rs = [r for r in records if r["api_level"] == level]
        if rs:
            first = sum(r["success_first"] for r in rs)
            final = sum(r["success_final"] for r in rs)
            print(f"{level}: 1 回目で成功 {first}/{len(rs)}、修正込みで成功 {final}/{len(rs)}")
    print(f"詳しい集計: python cap_summary.py {results_csv}")


if __name__ == "__main__":
    main()
