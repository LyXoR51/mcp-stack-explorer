from inspect import signature
from bench.data import TABLES

class ToolError(Exception):
    """Base class for errors raised by tool executors.

    Caught by execute_tool and mapped to an error_type.
    """


class BadArgumentError(ToolError):
    """Raised when an argument has an invalid type or value.

    Covers wrong type, out of range, not in enum, unknown column.
    """


class UnknownTableError(ToolError):
    """Raised when a requested table does not exist in TABLES."""


def _require_table(table: str) -> None:
    """Check that a table exists.

    Args:
        table: Table name.

    Raises:
        BadArgumentError: If table is not a string.
        UnknownTableError: If the table does not exist.
    """
    if not isinstance(table, str):
        message = f"table must be a string, got {type(table).__name__}"
        raise BadArgumentError(message)

    if table not in TABLES:
        message = f"table {table!r} unknown, use list_tables"
        raise UnknownTableError(message)


def list_tables() -> list[str]:
    """Return the table names, in insertion order.

    Returns:
        A new list of table names (modifying it does not affect TABLES).
    """
    return list(TABLES)


def describe_table(table: str) -> list[dict[str, str]]:
    """Describe the columns of a table.

    Column types are read from the first row only: wrong if a value is None.

    Args:
        table: Table name.

    Returns:
        One {"name": ..., "type": ...} dict per column, type as a string.

    Raises:
        BadArgumentError: If table is not a string.
        UnknownTableError: If the table does not exist.
    """
    _require_table(table)
    return [
        {"name": column, "type": type(value).__name__}
        for column, value in TABLES[table][0].items()
    ]


def count_rows(table: str) -> int:
    """Count the rows of a table.

    Args:
        table: Table name.

    Returns:
        The number of rows (0 for an empty table).

    Raises:
        BadArgumentError: If table is not a string.
        UnknownTableError: If the table does not exist.
    """
    _require_table(table)
    return len(TABLES[table])


def query_rows(
    table: str,
    limit: int,
    order: str,
    order_by: str | None = None,
) -> list[dict]:
    """Return the first rows of a table, sorted by a column.

    The table is sorted on a copy: TABLES is never modified. Columns are
    read from the first row, so an empty table raises IndexError (assumed:
    no table is empty in the fictional world).

    Args:
        table: Table name.
        limit: Maximum number of rows to return, an integer >= 1.
        order: Sort direction, "asc" or "desc".
        order_by: Column to sort on. Defaults to "id" when None.

    Returns:
        At most `limit` rows, as new dicts (modifying them does not
        affect TABLES).

    Raises:
        BadArgumentError: If table, limit, order or order_by has an
            invalid type or value (including an unknown column).
        UnknownTableError: If the table does not exist.
    """
    _require_table(table)
    columns = list(TABLES[table][0])

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        message = f"limit must be an integer >= 1, got {limit!r}"
        raise BadArgumentError(message)

    if order not in ("asc", "desc"):
        message = f"order must be 'asc' or 'desc', got {order!r}"
        raise BadArgumentError(message)

    if order_by is None:
        order_by = "id"
    if not isinstance(order_by, str):
        message = f"order_by must be a string, got {type(order_by).__name__}"
        raise BadArgumentError(message)
    if order_by not in columns:
        valid = ", ".join(columns)
        message = (
            f"order_by {order_by!r} unknown for table {table!r}, valid columns: {valid}"
        )
        raise BadArgumentError(message)

    rows = sorted(
        TABLES[table],
        key=lambda row: row[order_by],
        reverse=(order == "desc"),
    )
    return [dict(row) for row in rows[:limit]]


def table_info(table: str) -> dict:
    """Return the column names of a table.

    Names are read from the first row only, in insertion order. No types and
    no row count are returned (see describe_table and count_rows). An empty
    table raises IndexError (assumed: no table is empty in the fictional
    world).

    Args:
        table: Table name.

    Returns:
        A single dict {"table": <table name>, "columns": <list of column
        names>}.

    Raises:
        BadArgumentError: If table is not a string.
        UnknownTableError: If the table does not exist.
    """
    _require_table(table)
    return {"table": table, "columns": list(TABLES[table][0])}


EXECUTORS = {
    "list_tables": list_tables,
    "describe_table": describe_table,
    "count_rows": count_rows,
    "query_rows": query_rows,
    "table_info": table_info,
}


def _result(ok: bool, error_type: str | None, content: object) -> dict:
    """Build the dict returned by execute_tool.

    Single place that defines the result format.

    Args:
        ok: True if the tool ran without error.
        error_type: None on success, otherwise one of "unknown_tool",
            "bad_arguments", "unknown_table", "execution_error".
        content: The tool result on success, the readable error text sent
            back to the model on failure.

    Returns:
        A dict {"ok": ..., "error_type": ..., "content": ...}.
    """
    return {"ok": ok, "error_type": error_type, "content": content}


def execute_tool(name: object, arguments: object) -> dict:
    """Run a tool on behalf of the model and never raise.

    Anything the model sends is accepted as input: errors are returned in
    the result, not raised. The signature is checked with Signature.bind,
    so a TypeError raised during execution is a bench bug
    (execution_error), not a model mistake (bad_arguments).

    Args:
        name: Tool name sent by the model (any type, empty string included).
        arguments: Arguments sent by the model. Must be a dict: None is
            refused (strict bench, see the phase doc).

    Returns:
        {"ok": True, "error_type": None, "content": <tool result>} on
        success, otherwise {"ok": False, "error_type": <one of
        "unknown_tool", "bad_arguments", "unknown_table",
        "execution_error">, "content": <error text for the model>}.
    """
    # A non-str name is an unknown tool; isinstance comes first so that an
    # unhashable name never reaches the `in` test (it would raise TypeError).
    if not isinstance(name, str) or name not in EXECUTORS:
        # The message lists the valid names so the model can correct itself.
        return _result(
            False,
            "unknown_tool",
            f"{name!r} is not a valid tool, must be one of {list(EXECUTORS)}",
        )

    if not isinstance(arguments, dict):
        return _result(
            False,
            "bad_arguments",
            f"arguments must be a dict, got {type(arguments).__name__}",
        )

    fn = EXECUTORS[name]

    # Signature recomputed on each call: negligible cost, simpler code.
    # A non-str key in `arguments` also raises TypeError here.
    try:
        bound = signature(fn).bind(**arguments)
    except TypeError as exc:
        return _result(False, "bad_arguments", str(exc))

    # Order matters: Exception last, it would catch everything before it.
    try:
        result = fn(*bound.args, **bound.kwargs)
    except UnknownTableError as exc:
        return _result(False, "unknown_table", str(exc))
    except BadArgumentError as exc:
        return _result(False, "bad_arguments", str(exc))
    except Exception as exc:
        return _result(
            False,
            "execution_error",
            f"{type(exc).__name__}: {exc}",
        )

    return _result(True, None, result)
