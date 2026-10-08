"""Guided JSON generation: prompt for JSON, then extract, validate and repair.

A portable structured-output backend that needs only ``transformers`` — no
constrained-decoding library, no Rust, no quantizer — so it installs on any image.
It guarantees the *returned* value is schema-valid by validating and retrying; the
caller never receives invalid data (it raises instead).

N-ATLAS reliably produces the right content but wraps it in prose, ```json fences,
and often echoes the schema itself. So the backend extracts *every* JSON object in
the output and returns the first that validates against the schema, re-asking on a
miss with a plain-language description of the required fields.
"""

from __future__ import annotations

import json
from typing import Any

from .schema import SchemaError, to_json_schema, validate

__all__ = ["PromptedJsonBackend", "extract_json", "extract_json_candidates"]

_DECODER = json.JSONDecoder()


def extract_json_candidates(text: str) -> list[Any]:
    """Return every top-level JSON object found in ``text``, in order."""
    candidates: list[Any] = []
    index = 0
    while True:
        start = text.find("{", index)
        if start == -1:
            break
        try:
            obj, end = _DECODER.raw_decode(text[start:])
            candidates.append(obj)
            index = start + end
        except ValueError:
            index = start + 1
    return candidates


def extract_json(text: str) -> Any:
    """Return the first JSON object in ``text``.

    Raises:
        ValueError: If no JSON object is present.
    """
    candidates = extract_json_candidates(text)
    if not candidates:
        raise ValueError("no JSON object found in model output")
    return candidates[0]


def _describe_fields(schema: dict) -> str:
    properties = schema.get("properties", {})
    required = set(schema.get("required", list(properties)))
    parts = []
    for key, sub in properties.items():
        label = f'"{key}"'
        if isinstance(sub, dict) and sub.get("enum"):
            label += f" (one of: {', '.join(map(str, sub['enum']))})"
        elif isinstance(sub, dict) and sub.get("type"):
            label += f" ({sub['type']})"
        if key not in required:
            label += " [optional]"
        parts.append(label)
    return ", ".join(parts) if parts else "the fields in the schema"


def _instruction(prompt: str, schema: dict) -> str:
    return (
        f"{prompt}\n\n"
        f"Reply with ONLY a single JSON object using exactly these keys: "
        f"{_describe_fields(schema)}.\n"
        f"No markdown, no code fences, no explanation, no schema. JSON:"
    )


class PromptedJsonBackend:
    """Structured output via guided generation + extraction + validate/repair.

    Args:
        model: A loaded ``transformers`` causal LM.
        tokenizer: Its tokenizer.
        max_new_tokens: Generation cap per attempt.
        retries: Extra attempts if no candidate validates.
    """

    def __init__(
        self, model: Any, tokenizer: Any, *, max_new_tokens: int = 200, retries: int = 2
    ) -> None:
        self._model = model
        self._tokenizer = tokenizer
        self._max_new_tokens = max_new_tokens
        self._retries = retries
        self._device = model.get_input_embeddings().weight.device

    def _generate(self, text: str) -> str:
        inputs = self._tokenizer(text, return_tensors="pt").to(self._device)
        output = self._model.generate(
            **inputs,
            max_new_tokens=self._max_new_tokens,
            do_sample=False,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        return self._tokenizer.decode(
            output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )

    def generate_json(self, prompt: str, schema: dict) -> Any:
        schema_dict = to_json_schema(schema)
        instruction = _instruction(prompt, schema_dict)
        for _ in range(self._retries + 1):
            text = self._generate(instruction)
            for candidate in extract_json_candidates(text):
                try:
                    validate(candidate, schema_dict)
                    return candidate
                except SchemaError:
                    continue
            instruction = (
                _instruction(prompt, schema_dict)
                + "\nYour previous reply did not match. Use exactly the keys above."
            )
        raise SchemaError("no schema-valid JSON produced after retries")
