"""Guaranteed structured output and tool-calling for N-ATLAS (Pillar 1)."""

from .backend import StructuredBackend, StubBackend, minimal_instance
from .client import Structured
from .outlines_backend import OutlinesBackend
from .prompted_backend import PromptedJsonBackend, extract_json, extract_json_candidates
from .schema import SchemaError, to_json_schema, validate
from .tools import Tool, ToolCall, tool_choice_schema
from .transformers_backend import TransformersJsonBackend, first_json_object

__all__ = [
    "Structured",
    "StructuredBackend",
    "StubBackend",
    "PromptedJsonBackend",
    "extract_json",
    "extract_json_candidates",
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
