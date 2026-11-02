import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import httpx

from bench import cases, checks, client, schemas

BASE_URL = "http://localhost:11434"
NUM_CTX = 8192
TEMPERATURE = 0.5
BENCH_VERSION = 2
RESULTS_DIR = Path("bench/results")

CONFIGS = [
    {"config_id": 1, "model": "qwen3.5:9b", "digest": "56671c2ab938", "think": False},
    {"config_id": 2, "model": "nemotron-3.5-bolt:e4b","digest": "69f2be39b309","think": False},
    {"config_id": 3, "model": "llama3.1:8b", "digest": "46e0c10c039e", "think": False},
]


def run_once(config: dict, case: dict, run_idx: int) -> dict:
    """Play one case once and return one JSONL row (same keys on success and error)."""
    row = {
        "config_id": config["config_id"],
        "model": config["model"],
        "digest": config["digest"],
        "think": config["think"],
        "bench_version": BENCH_VERSION,
        "num_ctx": NUM_CTX,
        "temperature": TEMPERATURE,
        "case_id": case["id"],
        "run_idx": run_idx,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": None,
        "eval_count": None,
        "eval_duration": None,
        "total_duration": None,
        "load_duration": None,
        "prompt_eval_duration": None,
        "prompt_eval_count": None,
        "verdict": None,
        "error": None,
    }

    try:
        r = client.chat(
            base_url=BASE_URL,
            model=config["model"],
            messages=[{"role": "user", "content": case["prompt"]}],
            tools=schemas.get_schemas(cases.ALL_TOOLS),
            options={"num_ctx": NUM_CTX, "temperature": TEMPERATURE},
            think=config["think"],
        )
    except (RuntimeError, httpx.HTTPError) as exc:
        row["error"] = str(exc)
    else:
        message = r.get("message")
        row["message"] = message
        row["verdict"] = checks.check(message, case, cases.ALL_TOOLS)
        row["eval_count"] = r.get("eval_count")
        row["eval_duration"] = r.get("eval_duration")
        row["total_duration"] = r.get("total_duration")
        row["load_duration"] = r.get("load_duration")
        row["prompt_eval_duration"] = r.get("prompt_eval_duration")
        row["prompt_eval_count"] = r.get("prompt_eval_count")

    return row


def append_row(path: Path, row: dict) -> None:
    """Append one row as a single JSONL line."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(configs: list[dict], case_list: list[dict], n_runs: int = 5) -> Path:
    """Run the whole bench into a new timestamped file and return its path."""
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"bench_{stamp}.jsonl"
    print(f"Results: {path}")

    for config in configs:
        print(f"Config {config['config_id']}: {config['model']}")
        for run_idx in range(n_runs):
            for case in case_list:
                row = run_once(config, case, run_idx)
                append_row(path, row)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument(
        "--configs",
        type=int,
        nargs="*",
        help="config_id to play (default: all)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    selected = [
        c for c in CONFIGS if not args.configs or c["config_id"] in args.configs
    ]
    if not selected:
        raise SystemExit(f"No config matches {args.configs}")
    main(selected, cases.CASES, n_runs=args.runs)
