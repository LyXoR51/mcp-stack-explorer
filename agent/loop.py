import json

import httpx


def tool_message(res: dict) -> dict:
    """Turn an execute_tool result into the `tool` message sent to the model.

    Success: the content serialized as JSON. Failure: the error text,
    not serialized, prefixed with "Error: " so the model can tell it from data.
    Contract with any executor (local or MCP): res has "ok" and "content",
    and content is a string when ok is False.
    """
    if res["ok"]:
        content = json.dumps(res["content"], ensure_ascii=False)
    else:
        content = "Error: " + res["content"]
    return {"role": "tool", "content": content}


def run_agent(question, system, chat, execute_tool, max_turns=8, max_repeats=0) -> dict:
    """Run the agent loop until a final answer, a loop, or max_turns.

    Args:
        question: User question.
        system: System prompt.
        chat: Callable(messages) -> raw Ollama response dict. Tools and
            model settings are bound inside it. May raise RuntimeError or
            httpx.HTTPError, reported as "infra_error".
        execute_tool: Callable(name, arguments) -> {"ok", "error_type",
            "content"}. Must never raise.
        max_turns: Maximum number of model calls.
        max_repeats: Maximum number of tool call loops.

    Returns:
        Always the same keys: stop_reason ("final_answer", "loop",
        "max_turns", "infra_error"), answer (None unless final_answer),
        messages (raw history), turns (per-call metrics), error.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
    turns = []
    result = {
        "stop_reason": None,
        "answer": None,
        "messages": messages,
        "turns": turns,
        "error": None,
    }
    previous = None
    repeats = 0

    for _ in range(max_turns):
        try:
            r = chat(messages)
        except (RuntimeError, httpx.HTTPError) as exc:
            result["stop_reason"], result["error"] = "infra_error", str(exc)
            return result

        msg = r["message"]
        messages.append(msg)
        turns.append({
            "eval_count": r.get("eval_count"),
            "eval_duration": r.get("eval_duration"),
            "total_duration": r.get("total_duration"),
            "prompt_eval_count": r.get("prompt_eval_count"),
        })

        calls = msg.get("tool_calls") or []
        if not calls:
            result["stop_reason"] = "final_answer"
            result["answer"] = msg.get("content")
            return result

        parsed = []
        for call in calls:
            fn = call.get("function") or {}
            parsed.append((fn.get("name"), fn.get("arguments")))

        signature = [(name, json.dumps(args, sort_keys=True)) for name, args in parsed]
        if signature == previous:
            repeats += 1
            if repeats >= max_repeats:
                result["stop_reason"] = "loop"
                return result
        previous = signature

        for name, args in parsed:
            messages.append(tool_message(execute_tool(name, args)))

    result["stop_reason"] = "max_turns"
    return result