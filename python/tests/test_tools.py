import pytest

from gyara.structured import Tool, tool_choice_schema, validate

SEND = Tool(
    name="send_money",
    description="Send money to a contact",
    parameters={
        "type": "object",
        "properties": {"to": {"type": "string"}, "amount": {"type": "integer"}},
        "required": ["to", "amount"],
    },
)
CHECK = Tool(
    name="check_balance",
    description="Check the account balance",
    parameters={"type": "object", "properties": {}},
)


def test_tool_rejects_invalid_name():
    with pytest.raises(ValueError):
        Tool(name="send money", description="x", parameters={})


def test_tool_rejects_blank_description():
    with pytest.raises(ValueError):
        Tool(name="x", description="  ", parameters={})


def test_choice_schema_validates_correct_call():
    schema = tool_choice_schema([SEND, CHECK])
    validate({"tool": "send_money", "arguments": {"to": "Ada", "amount": 10}}, schema)
    validate({"tool": "check_balance", "arguments": {}}, schema)


def test_choice_schema_ties_arguments_to_the_chosen_tool():
    schema = tool_choice_schema([SEND, CHECK])
    from gyara.structured import SchemaError

    # Claiming send_money but omitting its required args must fail.
    with pytest.raises(SchemaError):
        validate({"tool": "send_money", "arguments": {}}, schema)
    # Wrong argument type for the chosen tool must fail.
    with pytest.raises(SchemaError):
        validate({"tool": "send_money", "arguments": {"to": "Ada", "amount": "lots"}}, schema)


def test_choice_schema_rejects_extra_top_level_keys():
    schema = tool_choice_schema([SEND])
    from gyara.structured import SchemaError

    with pytest.raises(SchemaError):
        validate(
            {"tool": "send_money", "arguments": {"to": "Ada", "amount": 10}, "x": 1},
            schema,
        )


def test_choice_schema_rejects_unknown_tool():
    schema = tool_choice_schema([SEND])
    from gyara.structured import SchemaError

    with pytest.raises(SchemaError):
        validate({"tool": "ghost", "arguments": {}}, schema)


def test_empty_and_duplicate_tools_rejected():
    with pytest.raises(ValueError):
        tool_choice_schema([])
    with pytest.raises(ValueError):
        tool_choice_schema([SEND, SEND])
