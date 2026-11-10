# mcp-stack-explorer

A local LLM agent that explores a Postgres database, a Qdrant instance and n8n workflows through a read-only MCP server running on a remote VPS.

> Educational project, built step by step and documented in public. Not production-ready.

## Goals

- Run the model locally (Ollama, GPU) and keep the agent loop dependency-light: no agent framework.
- Implement the MCP protocol by hand first, then compare with the official SDK.
- Guarantee read-only access at the source (database role and API key permissions), not only in the prompt.

## Architecture (target)

```
Local machine                          VPS
+---------------------------+          +--------------------------+
| Ollama (GPU)              |          | MCP server (container)   |
| Agent + MCP client        |--ssh---->| -> Postgres              |
+---------------------------+  stdio   | -> Qdrant                |
                                       | -> n8n                   |
                                       +--------------------------+
```

## Status

| Phase | Content                               | Status      |
|-------|---------------------------------------|-------------|
| 0     | Repo, Ollama on GPU, model comparison | Done        |
| 1     | Agent loop with a dummy local tool    | Done        |
| 2     | Minimal MCP server (1 tool) + client  | Planned     |
| 3     | Postgres tools                        | Planned     |
| 4     | Qdrant tools                          | Planned     |
| 5     | n8n tools                             | Planned     |
| 6     | CI/CD and comparison with the MCP SDK | Planned     |

## Repository layout

```
agent/    Product code: Ollama client and the agent loop
bench/    Test instrument: fictional tools, test cases, judges, run scripts
bench/results/  Raw JSONL results of the reference runs
docs/     Notes (Ollama setup)
```

`bench/` imports `agent/`, never the other way round. The agent loop receives its model call and its tool executor as parameters, so it does not know the fictional tools of the bench. The MCP client of phase 2 will provide the same two elements.

## Prerequisites

- Linux with an NVIDIA GPU and a working driver (`nvidia-smi`)
- Docker Engine and the NVIDIA Container Toolkit
- `nvidia` listed under `Runtimes` in `docker info`
- [uv](https://docs.astral.sh/uv/) for the Python environment

### Docker Desktop on Linux

Docker Desktop runs the Docker daemon inside a VM. According to Docker's documentation, GPU support in Docker Desktop is only available on Windows with the WSL 2 backend, so on Linux containers started through Docker Desktop will not get the GPU. Use the native Docker Engine:

```
docker context use default
docker info | grep -iE "runtimes|operating system"
```

## Quick start

```
docker compose up -d
docker compose exec ollama nvidia-smi
```

The second command must list your GPU. Ollama listens on `127.0.0.1:11434` only. Pulling models, checking GPU usage and the API: see [docs/ollama.md](docs/ollama.md).

The reference runs used Ollama 0.40.10 (image tag in `docker-compose.yaml`).

## Running the bench

Models must be pulled first (see [docs/ollama.md](docs/ollama.md)). Install the environment with `uv sync`, then run from the repository root:

```
# Single-turn cases (tool selection, arguments, no-tool question)
uv run python -m bench.runner --runs 20 --configs 1 2

# Chained case: the agent loop must combine several tool calls
uv run python -m bench.agent_runner --runs 10 --configs 1 2

# Recompute verdicts offline from a raw results file
uv run python -m bench.replay results/<file>.jsonl
```

Each run writes one JSON line with the full configuration and the raw message history, so results can be replayed without calling the model again.

## Results so far

Phase 0 and 1 compared `qwen3.5:9b` and `nemotron-3.5-bolt:e4b` on tool-calling reliability, on an RTX 4060 with 8 GB of VRAM, `num_ctx` 16384, temperature 0.5.

- **Single-turn cases** (6 cases, 20 runs each, thinking disabled): 117/120 for qwen, 118/120 for nemotron. Not a significant difference.
- **Chained case** (find the client of the most expensive intervention, which needs two tables), 10 runs per configuration:

| Model | Thinking disabled | Thinking enabled |
|-------|-------------------|------------------|
| qwen3.5:9b | 10/10 | 10/10 |
| nemotron-3.5-bolt:e4b | 0/10 | 10/10 |

- **Choice for the next phases:** `qwen3.5:9b` with thinking disabled. It is the fastest configuration that passes (median 8.6 s per run against about 20 s with thinking (median, first run excluded)). Nemotron passes only with thinking, where it is no faster than qwen.
- **How nemotron fails without thinking:** it reads one row of the second table, then repeats the same call until the loop detector stops it. It never asks for more rows.

### Limits

- One chained question and 10 runs per configuration: enough to separate these two models here, not to claim a success rate.
- The fictional `query_rows` tool has no filter, so the chained case partly measures how a model works around that. The Postgres tools of phase 3 will have one.
- Answers are judged by string matching, and failures were read by hand.
- Tool error messages in the bench tell the model what to do next, which a real MCP server may not.

## Configuration

Copy `.env.example` to `.env` and adjust the values. Never commit `.env`.

## Security notes

- This is a public repository: no secrets, test data only.
- Read-only access is enforced at the data source (planned for phases 3 to 5).

## License

[MIT](LICENSE)