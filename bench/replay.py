import json
import argparse
from collections import Counter, defaultdict
from statistics import median

from bench import executors


def load_rows(path: str) -> list[dict]:
    """Read a JSONL file, skip blank lines, report the line number on error."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {n}: invalid JSON") from exc
    return rows


def replay(row: dict) -> str | None:
    """Run the recorded tool calls through execute_tool.

    Returns None if there is nothing to replay (infra error, no structured
    call), "ok" if every call ran, otherwise the first error_type.
    """
    if row["error"] is not None or row["message"] is None:
        return None
    tool_calls = row["message"].get("tool_calls") or []
    if not tool_calls:
        return None
    for tool_call in tool_calls:
        function = tool_call.get("function") or {}
        result = executors.execute_tool(function.get("name"), function.get("arguments"))
        if not result["ok"]:
            return result["error_type"]
    return "ok"


def summarize(rows: list[dict]) -> tuple[dict, dict]:
    """Group by (config_id, case_id). Infra errors are counted apart."""
    cells = defaultdict(
        lambda: {"valid": 0, "errors": 0, "strict": 0,
                 "exec_ok": 0, "exec_n": 0, "both": 0, "types": Counter()}
    )
    labels = {}
    for row in rows:
        labels[row["config_id"]] = f"{row['model']} think={row['think']}"
        cell = cells[(row["config_id"], row["case_id"])]
        if row["error"] is not None:
            cell["errors"] += 1
            continue
        cell["valid"] += 1
        strict = row["verdict"] is None
        replayed = replay(row)
        cell["strict"] += strict
        if replayed is not None:
            cell["exec_n"] += 1
            cell["types"][replayed] += 1
            cell["exec_ok"] += replayed == "ok"
        if strict and replayed in (None, "ok"):
            cell["both"] += 1
    return cells, labels


def print_summary(cells: dict, labels: dict) -> None:
    for (config_id, case_id), c in sorted(cells.items()):
        exec_str = f"{c['exec_ok']}/{c['exec_n']}" if c["exec_n"] else "n/a"
        print(
            f"{labels[config_id]:32} {case_id:18} "
            f"strict {c['strict']}/{c['valid']}  exec {exec_str}  "
            f"both {c['both']}/{c['valid']}  infra_err {c['errors']}  "
            f"{dict(c['types'])}"
        )


def latency_table(rows):
    groups = defaultdict(list)
    for r in rows:
        if r["error"] is None and r["load_duration"] < 1_000_000_000:
            groups[(r["config_id"], r["case_id"])].append(r["total_duration"] / 1e9)
    for key, values in sorted(groups.items()):
        print(key, f"median {median(values):.2f}s  n={len(values)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        type=str,
        help="replay bench/results/xxx.jsonl",
        )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    rows = load_rows(args.file)
    print_summary(*summarize(rows))
    latency_table(rows)