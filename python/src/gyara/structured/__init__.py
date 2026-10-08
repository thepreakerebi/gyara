"""Guaranteed structured output and tool-calling for N-ATLAS (Pillar 1)."""

from .backend import StructuredBackend, StubBackend, minimal_instance
from .client import Structured
from .outlines_backend import OutlinesBackend
from .schema import SchemaError, to_json_schema, validate
from .tools import Tool, ToolCall, tool_choice_schema
from .transformers_backend import TransformersJsonBackend, first_json_object

__all__ = [
    "Structured",
    "StructuredBackend",
    "StubBackend",
    "OutlinesBackend",
    "TransformersJsonBackend",
    "first_json_object",
    "minimal_instance",
    "Tool",
    "ToolCall",
    "tool_choice_schema",
    "to_json_schema",
    "validate",
    "SchemaError",
]
