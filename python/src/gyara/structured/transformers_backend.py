"""Constrained JSON generation on a Transformers model (pure-Python, no Rust).

Uses lm-format-enforcer to mask the model's token choices so output always matches
the schema. Unlike the Outlines backend, its dependency installs as a wheel on any
Python, which is what makes it portable across Colab/Kaggle images.

The enforcement logic lives in lm-format-enforcer and transformers; this class just
wires a schema to the model. It needs a GPU model, so it is exercised on a GPU host
rather than in the local test suite (the parsing helper below is unit-tested).
"""

from __future__ import annotations

import json
from typing import Any

from .schema import to_json_schema

__all__ = ["TransformersJsonBackend", "first_json_object"]


def first_json_object(text: str) -> Any:
    """Parse the first JSON value in ``text``, ignoring any trailing tokens."""
    return json.JSONDecoder().raw_decode(text.strip())[0]


class TransformersJsonBackend:
    """A :class:`~gyara.structured.StructuredBackend` using a Transformers model.

    Args:
        model: A loaded ``transformers`` causal LM.
        tokenizer: Its tokenizer.
        max_new_tokens: Generation cap per call.
    """

    def __init__(self, model: Any, tokenizer: Any, *, max_new_tokens: int = 256) -> None:
        self._model = model
        self._tokenizer = tokenizer
        self._max_new_tokens = max_new_tokens
        self._input_device = model.get_input_embeddings().weight.device

    def generate_json(self, prompt: str, schema: dict) -> Any:
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.transformers import (
            build_transformers_prefix_allowed_tokens_fn,
        )

        schema_dict = to_json_schema(schema)
        parser = JsonSchemaParser(schema_dict)
        prefix_fn = build_transformers_prefix_allowed_tokens_fn(self._tokenizer, parser)

        full_prompt = f"{prompt}\nReturn only a JSON object.\n"
        inputs = self._tokenizer(full_prompt, return_tensors="pt").to(self._input_device)
        output = self._model.generate(
            **inputs,
            max_new_tokens=self._max_new_tokens,
            do_sample=False,
            prefix_allowed_tokens_fn=prefix_fn,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        completion = self._tokenizer.decode(
            output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        return first_json_object(completion)
