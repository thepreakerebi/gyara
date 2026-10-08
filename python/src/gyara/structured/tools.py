"""Tool definitions for structured tool-calling.

A :class:`Tool` pairs a name and description with a JSON Schema for its arguments.
:func:`tool_choice_schema` builds a single schema that forces the model to pick one
tool and fill arguments that validate against *that* tool — so a tool call is correct
by construction, not just plausible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import to_json_schema

__all__ = ["Tool", "ToolCall", "tool_choice_schema"]


@dataclass(frozen=True)
class Tool:
    """A callable the model may choose, with a JSON Schema for its arguments.

    Args:
        name: A valid identifier (e.g. ``"send_money"``).
        description: What the tool does, shown to the model.
        parameters: JSON Schema ``dict`` or Pydantic model for the arguments.
    """

    name: str
    description: str
    parameters: Any

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.isidentifier():
            raise ValueError(f"tool name must be a valid identifier, got {self.name!r}")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("tool description must be a non-empty string")

    @property
    def parameters_schema(self) -> dict:
        """The arguments schema as a JSON Schema ``dict``."""
        return to_json_schema(self.parameters)


@dataclass(frozen=True)
class ToolCall:
    """The model's choice: a tool name and its validated arguments."""

    name: str
    arguments: dict


def tool_choice_schema(tools: list[Tool]) -> dict:
    """Build a JSON Schema that admits exactly one valid tool call.

    The result is an object ``{"tool": <name>, "arguments": {...}}`` whose ``oneOf``
    branches tie each tool name to its own argument schema.

    Raises:
        ValueError: If ``tools`` is empty or has duplicate names.
    """
    if not tools:
        raise ValueError("tools must be a non-empty list")
    names = [t.name for t in tools]
    if len(set(names)) != len(names):
        raise ValueError("tool names must be unique")

    branches = [
        {
            "type": "object",
            "properties": {
                "tool": {"const": tool.name},
                "arguments": tool.parameters_schema,
            },
            "required": ["tool", "arguments"],
            "additionalProperties": False,
        }
        for tool in tools
    ]
    return {"oneOf": branches}
