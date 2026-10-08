import pytest
from pydantic import BaseModel

from gyara.structured import SchemaError, to_json_schema, validate


class Transfer(BaseModel):
    name: str
    amount: int


def test_dict_schema_passthrough():
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    assert to_json_schema(schema) is schema


def test_pydantic_model_to_schema():
    schema = to_json_schema(Transfer)
    assert schema["type"] == "object"
    assert set(schema["required"]) == {"name", "amount"}


def test_validate_accepts_conforming_data():
    validate({"name": "Chidi", "amount": 5000}, Transfer)  # no raise


def test_validate_rejects_bad_type():
    with pytest.raises(SchemaError):
        validate({"name": "Chidi", "amount": "lots"}, Transfer)


def test_validate_rejects_missing_required():
    with pytest.raises(SchemaError):
        validate({"name": "Chidi"}, Transfer)


def test_to_json_schema_rejects_unknown():
    with pytest.raises(TypeError):
        to_json_schema(42)
