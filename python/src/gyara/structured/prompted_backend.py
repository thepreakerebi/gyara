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


def _instruction(prompt: str, schema: dict) -> str:
    # This exact wording is known to elicit real values from N-ATLAS (e.g. the
    # transfer task returns the actual recipient and amount).
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
        # N-ATLAS is instruction-tuned: format as a user turn via the chat template,
        # or it echoes the prompt and degenerates. repetition_penalty stops `}}}}` loops.
        messages = [{"role": "user", "content": text}]
        try:
            input_ids = self._tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, return_tensors="pt"
            ).to(self._device)
        except Exception:  # noqa: BLE001 - tokenizer without a chat template
            input_ids = self._tokenizer(text, return_tensors="pt").input_ids.to(self._device)
        output = self._model.generate(
            input_ids=input_ids,
            max_new_tokens=self._max_new_tokens,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        return self._tokenizer.decode(output[0][input_ids.shape[1] :], skip_special_tokens=True)

    def raw_completion(self, prompt: str, schema: dict) -> str:
        """Return the model's raw text for the guided prompt (for diagnostics)."""
        return self._generate(_instruction(prompt, to_json_schema(schema)))

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
