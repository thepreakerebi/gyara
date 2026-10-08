"""Shared chat-template generation for N-ATLAS (GPU host only).

N-ATLAS is instruction-tuned, so prompts must be formatted as a user turn via the
tokenizer's chat template — a raw string makes it echo the prompt and degenerate.
This helper handles the version differences in ``apply_chat_template`` (some return a
tensor, others a BatchEncoding dict) and is used by both the runtime baseline and the
structured backend. It needs a GPU model, so it is not part of the local test suite.
"""

from __future__ import annotations

from typing import Any


def chat_generate(
    model: Any,
    tokenizer: Any,
    text: str,
    *,
    max_new_tokens: int = 256,
    repetition_penalty: float = 1.15,
) -> str:
    """Generate a completion for ``text`` as a single user turn; return the new text."""
    device = model.get_input_embeddings().weight.device
    messages = [{"role": "user", "content": text}]
    try:
        encoded = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
        )
    except TypeError:
        encoded = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        )
    except Exception:  # noqa: BLE001 - tokenizer without a chat template
        encoded = tokenizer(text, return_tensors="pt")

    if hasattr(encoded, "items"):
        inputs = {key: value.to(device) for key, value in encoded.items()}
    else:
        inputs = {"input_ids": encoded.to(device)}

    output = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        repetition_penalty=repetition_penalty,
        pad_token_id=tokenizer.eos_token_id,
    )
    prompt_length = inputs["input_ids"].shape[1]
    return tokenizer.decode(output[0][prompt_length:], skip_special_tokens=True)
