# mcp-stack-explorer

A local LLM agent that explores a Postgres database, a Qdrant instance and
n8n workflows through a read-only MCP server running on a remote VPS.

> Educational project, built step by step and documented in public.
> Not production-ready.

## Goals

- Run the model locally (Ollama, GPU) and keep the agent loop dependency-light:
  no agent framework.
- Implement the MCP protocol by hand first, then compare with the official SDK.
- Guarantee read-only access at the source (database role and API key
  permissions), not only in the prompt.

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

| Phase | Content                              | Status      |
|-------|--------------------------------------|-------------|
| 0     | Repo, Ollama on GPU, model comparison | In progress |
| 1     | Agent loop with a dummy local tool   | Planned     |
| 2     | Minimal MCP server (1 tool) + client | Planned     |
| 3     | Postgres tools                       | Planned     |
| 4     | Qdrant tools                         | Planned     |
| 5     | n8n tools                            | Planned     |
| 6     | CI/CD and comparison with the MCP SDK | Planned     |

## Prerequisites

- Linux with an NVIDIA GPU and a working driver (`nvidia-smi`)
- Docker Engine and the NVIDIA Container Toolkit
- `nvidia` listed under `Runtimes` in `docker info`

### Docker Desktop on Linux

Docker Desktop runs the Docker daemon inside a VM. According to Docker's
documentation, GPU support in Docker Desktop is only available on Windows with
the WSL 2 backend, so on Linux containers started through Docker Desktop will
not get the GPU. Use the native Docker Engine:

```
docker context use default
docker info | grep -iE "runtimes|operating system"
```

## Configuration

Copy `.env.example` to `.env` and adjust the values. Never commit `.env`.

## Security notes

- This is a public repository: no secrets, test data only.
- Read-only access is enforced at the data source (planned for phases 3 to 5).

## License

[MIT](LICENSE)