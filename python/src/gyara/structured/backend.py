"""Backends that turn a prompt + schema into structured data.

A real backend uses constrained decoding on N-ATLAS so output is schema-valid by
construction (added where the model runs). :class:`StubBackend` is a deterministic,
GPU-free stand-in for local development and tests.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

__all__ = ["StructuredBackend", "StubBackend", "minimal_instance"]


@runtime_checkable
class StructuredBackend(Protocol):
    """Produces data conforming to ``schema`` for a given ``prompt``."""

    def generate_json(self, prompt: str, schema: dict) -> Any: ...


def minimal_instance(schema: dict) -> Any:
    """Return a minimal value that satisfies ``schema``.

    Covers the JSON Schema subset Gyara emits (``const``, ``enum``, ``oneOf``/
    ``anyOf``, objects, arrays, and scalar types). Used by :class:`StubBackend` to
    synthesise valid output without a model.
    """
    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return schema["enum"][0]
    if schema.get("oneOf"):
        return minimal_instance(schema["oneOf"][0])
    if schema.get("anyOf"):
        return minimal_instance(schema["anyOf"][0])

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = schema_type[0]
    if schema_type is None and "properties" in schema:
        schema_type = "object"

    if schema_type == "object":
        properties = schema.get("properties", {})
        return {key: minimal_instance(sub) for key, sub in properties.items()}
    if schema_type == "array":
        count = schema.get("minItems", 0)
        item_schema = schema.get("items", {"type": "string"})
        return [minimal_instance(item_schema) for _ in range(count)]
    if schema_type == "string":
        return schema.get("default", "")
    if schema_type in ("integer", "number"):
        return schema.get("default", 0)
    if schema_type == "boolean":
        return schema.get("default", False)
    return None


class StubBackend:
    """Deterministic backend for tests and local dev.

    Returns ``response`` when given, otherwise synthesises a minimal valid instance
    of the schema. The prompt is ignored.
    """

    def __init__(self, response: Any = None) -> None:
        self._response = response
        self._has_response = response is not None

    def generate_json(self, prompt: str, schema: dict) -> Any:
        if self._has_response:
            return self._response
        return minimal_instance(schema)
