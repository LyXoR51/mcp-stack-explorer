def check(message: dict, case: dict, provided_tools: list[str]) -> str | None:
    """Check one assistant message against a single-turn case.

    Never raises on a malformed message. Every tool call is checked in
    order and the first failure decides the verdict.

    Only the keys present in case["expected_args"] are compared (value and
    type, so True does not match 1 and 3.0 does not match 3). Extra
    arguments are tolerated: invalid ones are caught by execute_tool.

    Args:
        message: The raw "message" dict from Ollama's response.
        case: A case from cases.py (expected_tools, expected_args).
        provided_tools: Names of the tools sent in the request.

    Returns:
        None on success, otherwise one of "no_call", "unknown_tool",
        "wrong_tool", "bad_args".
    """
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return None if not case["expected_tools"] else "no_call"

    for tool_call in tool_calls:
        function = tool_call.get("function") or {}

        name = function.get("name")
        if not isinstance(name, str) or name not in provided_tools:
            return "unknown_tool"
        if name not in case["expected_tools"]:
            return "wrong_tool"

        arguments = function.get("arguments")
        if not isinstance(arguments, dict):
            return "bad_args"

        for key, expected in case["expected_args"].items():
            if key not in arguments:
                return "bad_args"
            received = arguments[key]
            if received != expected or type(received) is not type(expected):
                return "bad_args"

    return None