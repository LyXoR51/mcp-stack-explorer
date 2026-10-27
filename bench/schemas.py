SCHEMAS = {
    "list_tables": {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": (
                "List the names of all tables in the database. "
                "Use it when you need to know which tables exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    "count_rows": {
        "type": "function",
        "function": {
            "name": "count_rows",
            "description": (
                "Count the rows of a table. "
                "Use it when you need to know the number of rows."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Name of the table to count the rows of.",
                    },
                },
                "required": ["table"],
            },
        },
    },
    "describe_table": {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": (
                "Describe the columns of a table. "
                "Use it when you need to know the name and type of each column."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Name of the table to describe.",
                    },
                },
                "required": ["table"],
            },
        },
    },
    "table_info": {
        "type": "function",
        "function": {
            "name": "table_info",
            "description": (
                "Get general information about a table. "
                "Use it when you need to know the column names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Name of the table to get information about.",
                    },
                },
                "required": ["table"],
            },
        },
    },
    "query_rows": {
        "type": "function",
        "function": {
            "name": "query_rows",
            "description": (
                "Return rows of a table, sorted by a column. "
                "Use it when you need to read the rows themselves."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Name of the table to read rows from.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return, at least 1.",
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort direction.",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Column to sort on. Defaults to id.",
                    },
                },
                "required": ["table", "limit", "order"],
            },
        },
    },
}


class UnknownSchemaError(Exception):
    """Raised when a requested schema name is not in SCHEMAS.

    A bench configuration bug, not a model mistake: it does not inherit
    from ToolError and is never mapped by execute_tool.
    """


def get_schemas(names: list[str]) -> list[dict]:
    """Return the schemas of the requested tools, in the requested order.

    The schemas are the objects stored in SCHEMAS, not copies: callers
    must not modify them. Duplicate names are not checked: they return
    the same schema twice.

    Args:
        names: Tool names, e.g. ["list_tables", "count_rows"].

    Returns:
        One schema dict per name, ready to send as the `tools` field.

    Raises:
        TypeError: If names is not a list.
        ValueError: If names is empty. To send no tool, pass tools=None
            to chat() instead.
        UnknownSchemaError: If one or more names are not in SCHEMAS.
    """
    if not isinstance(names, list):
        message = f"names must be a list, got {type(names).__name__}"
        raise TypeError(message)

    if not names:
        message = "names must not be empty, pass tools=None to send no tool"
        raise ValueError(message)

    valid = list(SCHEMAS)
    unknown = [name for name in names if name not in valid]
    if unknown:
        message = f"unknown schema names {unknown!r}, valid names: {', '.join(valid)}"
        raise UnknownSchemaError(message)

    return [SCHEMAS[name] for name in names]
