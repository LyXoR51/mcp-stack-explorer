"""Minimal hand-written MCP server over stdio (protocol revision 2026-07-28).

Reads one JSON-RPC message per line on stdin and writes one per line on
stdout. stdout is reserved for the protocol: logs must go to stderr.
"""

import json
import sys

from bench import executors, schemas

SUPPORTED_VERSIONS = ["2026-07-28"]
EXPOSED_TOOLS = ["count_rows"]
SERVER_INFO = {"name": "mcp-stack-explorer", "version": "1.0.0"}

META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"

# JSON-RPC / MCP error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
UNSUPPORTED_VERSION = -32022


def _result(request_id, result: dict) -> dict:
    """Wrap a result in a JSON-RPC response."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code: int, message: str, data=None) -> dict:
    """Build a JSON-RPC error response.

    The "id" key is left out when request_id is None (unreadable request).
    """
    response = {"jsonrpc": "2.0", "error": {"code": code, "message": message}}
    if request_id is not None:
        response["id"] = request_id
    if data is not None:
        response["error"]["data"] = data
    return response


def _discover_result() -> dict:
    return {
        "resultType": "complete",
        "supportedVersions": SUPPORTED_VERSIONS,
        "capabilities": {"tools": {}},
        "_meta": {META_SERVER_INFO: SERVER_INFO},
        "ttlMs": 0,
        "cacheScope": "public",
    }


def _to_mcp_tool(schema: dict) -> dict:
    """Convert an Ollama tool schema to the MCP tool format."""
    function = schema["function"]
    return {
        "name": function["name"],
        "description": function["description"],
        "inputSchema": function["parameters"],
    }


def _tools_list_result() -> dict:
    tools = [_to_mcp_tool(s) for s in schemas.get_schemas(EXPOSED_TOOLS)]
    return {
        "resultType": "complete",
        "tools": tools,
        "ttlMs": 0,
        "cacheScope": "public",
    }


def _tool_call_result(res: dict) -> dict:
    """Turn an execute_tool result into a tools/call result.

    Success: the content serialized as JSON text. Failure: the error text,
    with isError set so the model can read it and correct itself.
    """
    if res["ok"]:
        text = json.dumps(res["content"], ensure_ascii=False)
    else:
        text = res["content"]
    return {
        "resultType": "complete",
        "content": [{"type": "text", "text": text}],
        "isError": not res["ok"],
    }


def _validate(request: dict) -> dict | None:
    """Check params and the required _meta fields of a request.

    Returns an error response, or None if the request is valid.
    """
    request_id = request["id"]
    params = request.get("params", {})
    if not isinstance(params, dict):
        return _error(request_id, INVALID_PARAMS, "params must be an object")
    meta = params.get("_meta", {})
    if not isinstance(meta, dict):
        return _error(request_id, INVALID_PARAMS, "_meta must be an object")
    for key in (META_VERSION, META_CAPABILITIES):
        if key not in meta:
            return _error(request_id, INVALID_PARAMS, f"missing {key} in _meta")
    version = meta[META_VERSION]
    if version not in SUPPORTED_VERSIONS:
        return _error(
            request_id,
            UNSUPPORTED_VERSION,
            "protocol version not supported",
            {"supported": SUPPORTED_VERSIONS, "requested": version},
        )
    return None


def handle(request: object) -> dict | None:
    """Return the response to one decoded message, or None if none is due.

    Notifications (no "id") get no response.
    """
    if not isinstance(request, dict):
        return _error(None, INVALID_REQUEST, "request must be an object")
    if "id" not in request:
        return None
    request_id = request["id"]
    method = request.get("method")

    if method == "server/discover":
        return _result(request_id, _discover_result())

    if method not in ("tools/list", "tools/call"):
        return _error(request_id, METHOD_NOT_FOUND, "method not found")

    error = _validate(request)
    if error is not None:
        return error

    if method == "tools/list":
        return _result(request_id, _tools_list_result())

    params = request["params"]
    name = params.get("name")
    if name not in EXPOSED_TOOLS:
        return _error(request_id, INVALID_PARAMS, "unknown tool")
    res = executors.execute_tool(name, params.get("arguments"))
    return _result(request_id, _tool_call_result(res))


def send(message: dict) -> None:
    """Write one message as a single JSON line on stdout and flush."""
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main() -> None:
    """Read stdin line by line until it is closed."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            send(_error(None, PARSE_ERROR, "invalid JSON"))
            continue
        response = handle(request)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()