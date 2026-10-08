"""Tests for OutlinesBackend using a fake Outlines (no model, no GPU)."""

import json

from gyara.structured import OutlinesBackend, Structured


class FakeOutlines:
    """Records how many generators it builds, and returns schema-valid JSON strings."""

    def __init__(self):
        self.builds = 0

    def factory(self, model, schema_str):
        self.builds += 1
        schema = json.loads(schema_str)

        def generate(prompt):
            # Minimal valid object for the (flat) schema, as a JSON string.
            obj = {key: _default(sub) for key, sub in schema.get("properties", {}).items()}
            return json.dumps(obj)

        return generate


def _default(sub):
    return {"string": "x", "integer": 1, "number": 1, "boolean": True}.get(sub.get("type"), None)


SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "amount": {"type": "integer"}},
    "required": ["name", "amount"],
}


def test_parses_json_string_into_dict():
    fake = FakeOutlines()
    backend = OutlinesBackend(model=object(), generator_factory=fake.factory)
    result = backend.generate_json("prompt", SCHEMA)
    assert result == {"name": "x", "amount": 1}


def test_caches_generator_per_schema():
    fake = FakeOutlines()
    backend = OutlinesBackend(model=object(), generator_factory=fake.factory)
    backend.generate_json("a", SCHEMA)
    backend.generate_json("b", SCHEMA)  # same schema -> reuse generator
    assert fake.builds == 1


def test_passes_through_non_string_result():
    def factory(model, schema_str):
        return lambda prompt: {"already": "parsed"}

    backend = OutlinesBackend(model=object(), generator_factory=factory)
    assert backend.generate_json("p", {"type": "object"}) == {"already": "parsed"}


def test_works_as_backend_for_structured_client():
    fake = FakeOutlines()
    client = Structured(OutlinesBackend(model=object(), generator_factory=fake.factory))
    assert client.generate("extract", SCHEMA) == {"name": "x", "amount": 1}
