"""Guided JSON generation: prompt for JSON, then extract, validate and repair.

A portable structured-output backend that needs only ``transformers`` — no
constrained-decoding library, no Rust, no quantizer — so it installs on any image.
It guarantees the *returned* value is schema-valid by validating and retrying; the
caller never receives invalid data (it raises instead).

N-ATLAS reliably produces the right content but wraps it in prose or ```json code
fences, which naive ``json.loads`` rejects. :func:`extract_json` recovers the object,
and the backend re-asks on a miss.
"""

from __future__ import annotations

import json
from typing import Any

from .schema import SchemaError, to_json_schema, validate

__all__ = ["PromptedJsonBackend", "extract_json"]


def extract_json(text: str) -> Any:
    """Return the first JSON object in ``text``, ignoring prose and code fences.

    Raises:
        ValueError: If no JSON object is present.
    """
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object found in model output")
    return json.JSONDecoder().raw_decode(text[start:])[0]


def _instruction(prompt: str, schema: dict) -> str:
    return (
        f"{prompt}\n\nRespond with ONLY a JSON object matching this schema "
        f"(no markdown, no explanation):\n{json.dumps(schema)}\nJSON:"
    )


class PromptedJsonBackend:
    """Structured output via guided generation + extraction + validate/repair.

    Args:
        model: A loaded ``transformers`` causal LM.
        tokenizer: Its tokenizer.
        max_new_tokens: Generation cap per attempt.
        retries: Extra attempts if the first reply is invalid.
    """

    def __init__(
        self, model: Any, tokenizer: Any, *, max_new_tokens: int = 200, retries: int = 1
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
        last_error: Exception | None = None
        for _ in range(self._retries + 1):
            text = self._generate(instruction)
            try:
                obj = extract_json(text)
                validate(obj, schema_dict)
                return obj
            except (ValueError, SchemaError) as error:
                last_error = error
                instruction = (
                    _instruction(prompt, schema_dict)
                    + "\nYour previous reply was not valid. Return only the JSON object."
                )
        raise last_error if last_error else ValueError("generation failed")
