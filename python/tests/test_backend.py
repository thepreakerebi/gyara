from gyara.structured import StubBackend, Tool, tool_choice_schema, validate
from gyara.structured.backend import minimal_instance


def test_stub_returns_preset_response():
    backend = StubBackend(response={"name": "Ada", "amount": 10})
    assert backend.generate_json("anything", {}) == {"name": "Ada", "amount": 10}


def test_minimal_instance_covers_scalar_types():
    assert minimal_instance({"type": "string"}) == ""
    assert minimal_instance({"type": "integer"}) == 0
    assert minimal_instance({"type": "boolean"}) is False
    assert minimal_instance({"const": "x"}) == "x"
    assert minimal_instance({"enum": ["a", "b"]}) == "a"


def test_minimal_instance_builds_valid_object():
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "amount": {"type": "integer"}},
        "required": ["name", "amount"],
    }
    instance = minimal_instance(schema)
    validate(instance, schema)  # synthesised instance must be schema-valid


def test_minimal_instance_satisfies_tool_choice_schema():
    tool = Tool(
        name="send_money",
        description="Send money",
        parameters={
            "type": "object",
            "properties": {"to": {"type": "string"}},
            "required": ["to"],
        },
    )
    schema = tool_choice_schema([tool])
    instance = minimal_instance(schema)
    validate(instance, schema)
    assert instance["tool"] == "send_money"


def test_minimal_instance_respects_min_items():
    schema = {"type": "array", "items": {"type": "string"}, "minItems": 2}
    assert minimal_instance(schema) == ["", ""]
