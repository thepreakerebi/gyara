"""High-level structured-output client (Pillar 1).

Ties a prompt and a schema to a backend, and validates the result as a safety net —
so callers always get schema-valid data or a clear error, never half-parsed text.
"""

from __future__ import annotations

from typing import Any

from .backend import StructuredBackend
from .schema import to_json_schema, validate
from .tools import Tool, ToolCall, tool_choice_schema

__all__ = ["Structured"]


class Structured:
    """Guaranteed structured output over any :class:`StructuredBackend`.

    Args:
        backend: Something with a ``generate_json(prompt, schema)`` method — a
            constrained-decoding backend in production, or ``StubBackend`` locally.
    """

    def __init__(self, backend: StructuredBackend) -> None:
        if not hasattr(backend, "generate_json"):
            raise TypeError("backend must implement generate_json(prompt, schema)")
        self._backend = backend

    def generate(self, prompt: str, schema: Any) -> Any:
        """Return data for ``prompt`` that conforms to ``schema``.

        Args:
            prompt: The instruction for the model.
            schema: JSON Schema ``dict`` or Pydantic model class.

        Raises:
            SchemaError: If the backend returns data that fails validation.
        """
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a str")
        json_schema = to_json_schema(schema)
        data = self._backend.generate_json(prompt, json_schema)
        validate(data, json_schema)
        return data

    def call_tool(self, prompt: str, tools: list[Tool]) -> ToolCall:
        """Choose one tool for ``prompt`` and return its validated arguments.

        Raises:
            SchemaError: If the chosen call fails validation.
            ValueError: If ``tools`` is empty or has duplicate names.
        """
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a str")
        schema = tool_choice_schema(tools)
        data = self._backend.generate_json(prompt, schema)
        validate(data, schema)
        return ToolCall(name=data["tool"], arguments=data["arguments"])
