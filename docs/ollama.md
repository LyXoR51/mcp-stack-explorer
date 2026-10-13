# Running Ollama

Make sure the native Docker Engine is the active context (see
[Prerequisites](../README.md#prerequisites)), then start Ollama:

```
docker compose up -d
```

The Ollama image is pinned in `docker-compose.yaml` for reproducibility. The API is
published on `127.0.0.1:11434` only: it has no authentication and must not be
exposed on the network.

### Pull a model

```
docker compose exec ollama ollama pull qwen3:8b
docker compose exec ollama ollama list
```

Models are stored in the `ollama` Docker volume and survive restarts.

### Check that the GPU is used

```
docker compose exec ollama nvidia-smi
```

The command must list your GPU. Then load a model and check where it runs:

```
docker compose exec ollama ollama run qwen3:8b "Say hello"
docker compose exec ollama ollama ps
```

The `PROCESSOR` column should read `100% GPU`. Any CPU share means part of the
model did not fit in VRAM.

### Check the API from the host

```
curl http://127.0.0.1:11434/api/tags
```

This returns the list of downloaded models as JSON.

### Stop

```
docker compose down
```

Do not add `-v`: it also deletes the volume, and with it every downloaded model
(several GB each).