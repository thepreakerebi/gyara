import pytest
from pydantic import BaseModel

from gyara.structured import SchemaError, Structured, StubBackend, Tool


class Transfer(BaseModel):
    name: str
    amount: int


def test_generate_returns_valid_data_from_stub():
    client = Structured(StubBackend(response={"name": "Chidi", "amount": 5000}))
    result = client.generate("Send 5k to Chidi", Transfer)
    assert result == {"name": "Chidi", "amount": 5000}


def test_generate_synthesises_valid_data_when_backend_has_no_preset():
    client = Structured(StubBackend())
    result = client.generate("anything", Transfer)
    assert set(result) == {"name", "amount"}  # minimal but schema-valid


def test_generate_raises_when_backend_output_invalid():
    client = Structured(StubBackend(response={"name": "Chidi"}))  # missing amount
    with pytest.raises(SchemaError):
        client.generate("Send money", Transfer)


def test_call_tool_returns_toolcall():
    send = Tool(
        name="send_money",
        description="Send money to a contact",
        parameters={
            "type": "object",
            "properties": {"to": {"type": "string"}, "amount": {"type": "integer"}},
            "required": ["to", "amount"],
        },
    )
    response = {"tool": "send_money", "arguments": {"to": "Ada", "amount": 10}}
    client = Structured(StubBackend(response=response))
    call = client.call_tool("Send 10 to Ada", [send])
    assert call.name == "send_money"
    assert call.arguments == {"to": "Ada", "amount": 10}


def test_backend_without_generate_json_rejected():
    with pytest.raises(TypeError):
        Structured(object())
