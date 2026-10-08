"""Gyara — a reliability layer for N-ATLAS.

Gyara makes Nigeria's sovereign LLM safe to build real products on:

- **Normalization (Pillar 2):** clean Nigerian-language input and fit it to the
  model's 8,092-token context window. Pure stdlib, available now via
  :mod:`gyara.normalize`.
- **Structured output (Pillar 1):** guaranteed schema-valid generation and
  tool-calling. Added in a later milestone; depends on the model runtime.
"""

from .normalize import (
    NATLAS_CONTEXT_LIMIT,
    DictionaryRestorer,
    Restorer,
    TokenBudget,
    TokenReport,
    normalize_text,
    strip_diacritics,
)
from .structured import (
    SchemaError,
    Structured,
    StructuredBackend,
    StubBackend,
    Tool,
    ToolCall,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Pillar 2 — normalization
    "normalize_text",
    "strip_diacritics",
    "DictionaryRestorer",
    "Restorer",
    "TokenBudget",
    "TokenReport",
    "NATLAS_CONTEXT_LIMIT",
    # Pillar 1 — structured output
    "Structured",
    "StructuredBackend",
    "StubBackend",
    "Tool",
    "ToolCall",
    "SchemaError",
]
