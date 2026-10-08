"""JSON Schema handling for structured output.

Accepts either a plain JSON Schema ``dict`` or a Pydantic model class, and validates
data against it. ``jsonschema`` and ``pydantic`` are optional (the ``structured``
extra) and imported lazily, so importing :mod:`gyara` stays dependency-free.
"""

from __future__ import annotations

from typing import Any

__all__ = ["to_json_schema", "validate", "SchemaError"]


class SchemaError(ValueError):
    """Raised when data does not conform to its schema."""


def to_json_schema(schema: Any) -> dict:
    """Return a JSON Schema ``dict`` for ``schema``.

    ``schema`` may be a JSON Schema ``dict`` (returned unchanged) or a Pydantic
    ``BaseModel`` subclass (converted via ``model_json_schema``).

    Raises:
        TypeError: If ``schema`` is neither of the above.
    """
    if isinstance(schema, dict):
        return schema
    model_json_schema = getattr(schema, "model_json_schema", None)
    if callable(model_json_schema):
        return model_json_schema()
    raise TypeError("schema must be a JSON Schema dict or a Pydantic BaseModel subclass")


def validate(data: Any, schema: Any) -> None:
    """Validate ``data`` against ``schema``; return ``None`` or raise.

    Raises:
        SchemaError: If ``data`` does not conform to the schema.
        ImportError: If the ``structured`` extra is not installed.
    """
    json_schema = to_json_schema(schema)
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - depends on install extras
        raise ImportError(
            "structured output requires jsonschema: pip install 'gyara[structured]'"
        ) from exc
    try:
        jsonschema.validate(instance=data, schema=json_schema)
    except jsonschema.ValidationError as exc:
        raise SchemaError(exc.message) from exc
