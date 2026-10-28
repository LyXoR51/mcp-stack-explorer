"""Single-turn test cases (cases 1 to 4 of the bench).

Pure data: no logic. Each case is a dict:
    id: stable identifier, copied into the JSONL, unique in CASES.
    prompt: the user question, in French.
    expected_tools: set of accepted tool names. Empty set = no call expected.
    expected_args: dict of expected arguments, only the keys that must be
        checked (other valid arguments are tolerated). {} = a call without
        arguments. None = no call expected (only when expected_tools is empty).

All tools in ALL_TOOLS are offered in every case, otherwise tool selection
is not measured. Prompts name the table when one is needed: discovering
tables is the job of case 5.
"""

ALL_TOOLS = [
    "list_tables",
    "count_rows",
    "describe_table",
    "table_info",
    "query_rows",
]

CASE_1 = {
    "id": "c1_list",
    "prompt": "Quelles tables sont disponibles ?",
    "expected_tools": {"list_tables"},
    "expected_args": {},
}

CASE_2 = {
    "id": "c2_no_tool",
    "prompt": "Combien font 12 × 8 ?",
    "expected_tools": set(),
    "expected_args": None,
}

CASE_3A = {
    "id": "c3a_count",
    "prompt": "Combien de lignes dans pieces_stock ?",
    "expected_tools": {"count_rows"},
    "expected_args": {"table": "pieces_stock"},
}

CASE_3B = {
    "id": "c3b_describe",
    "prompt": "Quels sont les types de colonnes dans clientele ?",
    "expected_tools": {"describe_table"},
    "expected_args": {"table": "clientele"},
}

# Deliberate ambiguity: describe_table and table_info both answer.
CASE_3C = {
    "id": "c3c_describe_info",
    "prompt": "Quelles sont les colonnes dans interventions ?",
    "expected_tools": {"describe_table", "table_info"},
    "expected_args": {"table": "interventions"},
}

# order_by is not checked: the model cannot know the column names at this
# point. Sorting by id or by inscrit_le gives the same rows (ids 4 and 3),
# so the case does not tell the two apart.
CASE_4 = {
    "id": "c4_query",
    "prompt": "Qui sont les deux derniers inscrits ?",
    "expected_tools": {"query_rows"},
    "expected_args": {"table": "clientele", "limit": 2, "order": "desc"},
}

CASES = [CASE_1, CASE_2, CASE_3A, CASE_3B, CASE_3C, CASE_4]