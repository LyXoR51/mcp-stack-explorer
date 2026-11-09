# bench/agent_runner.py
import argparse
from datetime import datetime, timezone
from pathlib import Path

from agent import client
from agent.loop import run_agent
from bench import cases, executors, schemas
from bench.runner import append_row

BASE_URL = "http://localhost:11434"
NUM_CTX = 16384
TEMPERATURE = 0.5
MAX_TURNS = 8
AGENT_BENCH_VERSION = 1
RESULTS_DIR = Path("bench/results")

SYSTEM = (
    "répondre en français, utiliser les outils pour lire la base, "
    "ne rien inventer, signaler une erreur d'outil."
)

CASE_5 = {
    "id": "c5_chain",
    "prompt": "Quel client a l’intervention la plus coûteuse ?",
    "expected_name": "inès marchand",
    "forbidden_name": "malo girard",
    "expected_cost": "89.9",  # compared after replacing "," with "."
}

CONFIGS = [
    {"config_id": 1, "model": "qwen3.5:9b", "digest": "56671c2ab938", "think": False},
    {"config_id": 2, "model": "nemotron-3.5-bolt:e4b", "digest": "69f2be39b309", "think": False},
    {"config_id": 3, "model": "qwen3.5:9b", "digest": "56671c2ab938", "think": True},
    {"config_id": 4, "model": "nemotron-3.5-bolt:e4b", "digest": "69f2be39b309", "think": True},
]


def make_chat(config: dict):
    """Bind tools and model settings so the loop only sees chat(messages)."""
    tools = schemas.get_schemas(cases.ALL_TOOLS)
    options = {"num_ctx": NUM_CTX, "temperature": TEMPERATURE}

    def chat(messages):
        return client.chat(BASE_URL, config["model"], messages, tools, options, config["think"])

    return chat


def judge(result: dict, case: dict) -> tuple[str, str | None]:
    """Return (verdict, fail_reason). verdict: "pass", "fail" or "infra_error"."""
    if result["stop_reason"] == "infra_error":
        return "infra_error", None
    if result["stop_reason"] != "final_answer":
        return "fail", result["stop_reason"]
    answer = (result["answer"] or "").lower().replace(",", ".")
    if case["forbidden_name"] in answer:
        return "fail", "forbidden_name"
    if case["expected_name"] not in answer or case["expected_cost"] not in answer:
        return "fail", "missing_expected"
    return "pass", None


def run_one(config: dict, case: dict, run_idx: int, max_repeats: int) -> dict:
    result = run_agent(
        case["prompt"],
        SYSTEM,
        make_chat(config),
        executors.execute_tool,
        max_turns=MAX_TURNS,
        max_repeats=max_repeats,
    )
    verdict, fail_reason = judge(result, case)
    return {
        "config_id": config["config_id"],
        "model": config["model"],
        "digest": config["digest"],
        "think": config["think"],
        "bench_version": AGENT_BENCH_VERSION,
        "num_ctx": NUM_CTX,
        "temperature": TEMPERATURE,
        "max_turns": MAX_TURNS,
        "max_repeats": max_repeats,
        "system": SYSTEM,
        "case_id": case["id"],
        "run_idx": run_idx,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "fail_reason": fail_reason,
        "stop_reason": result["stop_reason"],
        "answer": result["answer"],
        "messages": result["messages"],
        "turns": result["turns"],
        "error": result["error"],
    }


def main(configs: list[dict], n_runs: int, max_repeats: int) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"agent_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    print(f"Results: {path}")
    for config in configs:
        print(f"Config {config['config_id']}: {config['model']} think={config['think']}")
        for run_idx in range(n_runs):
            row = run_one(config, CASE_5, run_idx, max_repeats)
            append_row(path, row)
            detail = row["fail_reason"] or row["stop_reason"]
            print(f"  run {run_idx}: {row['verdict']} ({detail}, {len(row['turns'])} calls)")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--max-repeats", type=int, default=0)
    parser.add_argument("--configs", type=int, nargs="*", help="config_id to play (default: all)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    selected = [c for c in CONFIGS if not args.configs or c["config_id"] in args.configs]
    if not selected:
        raise SystemExit(f"No config matches {args.configs}")
    main(selected, args.runs, args.max_repeats)