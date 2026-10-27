import httpx

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60.0
WRITE_TIMEOUT = 10
POOL_TIMEOUT = 10

timeout = httpx.Timeout(
    connect=CONNECT_TIMEOUT,
    read=READ_TIMEOUT,
    write=WRITE_TIMEOUT,
    pool=POOL_TIMEOUT,
)
client = httpx.Client(timeout=timeout)


def build_payload(
    model: str,
    messages: list[dict],
    tools: list[dict] | None,
    options: dict | None,
    think: bool | None,
) -> dict:
    """Build the JSON body for Ollama's /api/chat endpoint.

    Pure function: no network access, so it can be tested without Ollama.

    Optional fields (tools, options, think) are included only when they are
    not None. In particular, think=False is sent (it disables reasoning),
    whereas think=None leaves the field out (model default). An empty
    options dict is sent as-is.

    Args:
        model: Model tag, e.g. "qwen3.5:9b".
        messages: Full conversation history, sent as-is.
        tools: Tool schemas, or None to send no tools.
        options: Runtime options (temperature, num_ctx, seed...), or None.
        think: True/False to force the reasoning mode, None for the default.

    Returns:
        The payload dict, always with stream=False.
    """
    payload = {"model": model, "messages": messages, "stream": False}
    if tools is not None:
        payload["tools"] = tools
    if options is not None:
        payload["options"] = options
    if think is not None:
        payload["think"] = think
    return payload


def chat(
    base_url: str,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    options: dict | None = None,
    think: bool | None = None,
) -> dict:
    """Send one non-streaming request to Ollama's /api/chat and return the raw JSON.

    The response is returned untouched (message, tool_calls, thinking,
    durations in nanoseconds, eval_count...): extracting fields is the
    caller's job.

    Args:
        base_url: Server address WITHOUT a trailing slash,
            e.g. "http://localhost:11434". The path "/api/chat" is appended.
        model, messages, tools, options, think: see build_payload().

    Returns:
        The decoded JSON response.

    Raises:
        RuntimeError: On an HTTP error status (4xx/5xx). The message includes
            the status code and Ollama's response body, e.g. a 400 when a
            model rejects think=True.
        httpx.ConnectError, httpx.ReadTimeout: Network errors are not caught
            and propagate to the caller.
    """
    payload = build_payload(model, messages, tools, options, think)
    r = client.post(base_url + "/api/chat", json=payload)
    if r.is_error:
        raise RuntimeError(f"Ollama returned HTTP {r.status_code}: {r.text}")
    return r.json()
