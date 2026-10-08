"""Constrained-decoding backend for N-ATLAS, built on Outlines.

This is the real backend behind :class:`~gyara.structured.Structured`: it masks the
model's token choices so output always matches the schema. It runs where the model
runs (a GPU host); import stays light because Outlines is only imported when a
generator is actually built.

The schema-to-generator wiring is injectable (``generator_factory``), so the parsing
and caching logic here is unit-tested with a fake Outlines, while the live model is
exercised on Kaggle.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from .schema import to_json_schema

__all__ = ["OutlinesBackend"]

# (model, json_schema_string) -> (prompt -> str | dict)
GeneratorFactory = Callable[[Any, str], Callable[[str], Any]]


def _default_factory(model: Any, schema_str: str) -> Callable[[str], Any]:
    import outlines  # imported lazily; only available in the `model` extra

    return outlines.generate.json(model, schema_str)


class OutlinesBackend:
    """A :class:`~gyara.structured.StructuredBackend` backed by Outlines.

    Args:
        model: An Outlines model (e.g. ``outlines.models.transformers(...)``).
        generator_factory: Builds a generator from ``(model, schema_str)``. Defaults
            to ``outlines.generate.json``; override it in tests.
    """

    def __init__(self, model: Any, *, generator_factory: GeneratorFactory | None = None) -> None:
        self._model = model
        self._factory = generator_factory or _default_factory
        self._cache: dict[str, Callable[[str], Any]] = {}

    def generate_json(self, prompt: str, schema: dict) -> Any:
        """Generate schema-constrained output for ``prompt``.

        Generators are cached per schema so repeated calls don't recompile the
        decoding constraints.
        """
        schema_dict = to_json_schema(schema)
        key = json.dumps(schema_dict, sort_keys=True)
        generator = self._cache.get(key)
        if generator is None:
            generator = self._factory(self._model, key)
            self._cache[key] = generator
        result = generator(prompt)
        return json.loads(result) if isinstance(result, str) else result
