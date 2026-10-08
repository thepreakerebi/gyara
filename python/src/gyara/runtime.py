"""Model runtime helpers for N-ATLAS (GPU host only).

These load the gated N-ATLAS weights and wire them to Gyara. The heavy libraries
(``transformers``, ``torch``, ``outlines``) are imported lazily, so importing
:mod:`gyara` needs none of them. Run these on a GPU host (Kaggle/Colab); they are not
part of the local test suite.

The one pure helper, :func:`encoder_from_tokenizer`, connects any tokenizer to
:class:`gyara.normalize.TokenBudget` and is unit-tested with a fake tokenizer.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

__all__ = [
    "resolve_token",
    "load_dotenv",
    "encoder_from_tokenizer",
    "load_natlas",
    "raw_generate",
    "load_outlines_model",
    "DEFAULT_MODEL_ID",
]

DEFAULT_MODEL_ID = "NCAIR1/N-ATLaS"


def load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    """Load simple ``KEY=VALUE`` lines from a ``.env`` file into ``os.environ``.

    Minimal and dependency-free; existing environment variables are not overwritten.
    Missing files are ignored. On a GPU host, prefer the platform's secret store.
    """
    file = Path(path)
    if not file.is_file():
        return
    for raw in file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def resolve_token(token: str | None = None) -> str:
    """Return the Hugging Face token, from the argument or ``HF_TOKEN``.

    Raises:
        RuntimeError: If no token is found.
    """
    resolved = token or os.environ.get("HF_TOKEN")
    if not resolved:
        raise RuntimeError(
            "No Hugging Face token. Set HF_TOKEN (env or Kaggle Secret) or pass token=."
        )
    return resolved


def encoder_from_tokenizer(tokenizer: Any) -> Callable[[str], Sequence[int]]:
    """Adapt a Hugging Face tokenizer to the ``str -> token-ids`` encoder TokenBudget needs."""
    if not hasattr(tokenizer, "encode"):
        raise TypeError("tokenizer must have an .encode(text) method")

    def encode(text: str) -> Sequence[int]:
        return tokenizer.encode(text, add_special_tokens=False)

    return encode


def load_natlas(
    model_id: str = DEFAULT_MODEL_ID, *, token: str | None = None, load_in_4bit: bool = False
) -> tuple[Any, Any]:
    """Load N-ATLAS once and return ``(model, tokenizer)``.

    Defaults to fp16 with ``device_map="auto"``, which shards the 8B model across
    available GPUs (e.g. Kaggle's 2x T4 = 32 GB) and tolerates CPU offload if memory
    is tight. Set ``load_in_4bit=True`` only on a single 16 GB GPU with bitsandbytes
    available (it refuses to load if anything spills to CPU). Frees leftover GPU
    memory first, so repeated runs in one kernel don't accumulate.
    """
    import gc

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    auth = resolve_token(token)
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=auth)

    kwargs: dict[str, Any] = {"token": auth, "device_map": "auto"}
    if load_in_4bit:
        try:
            import bitsandbytes  # noqa: F401  # ensure the backend is installed
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        except Exception:  # noqa: BLE001 - no bitsandbytes: fall back to fp16
            kwargs["torch_dtype"] = torch.float16
    else:
        kwargs["torch_dtype"] = torch.float16

    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    return model, tokenizer


def raw_generate(model: Any, tokenizer: Any, prompt: str, max_new_tokens: int = 256) -> str:
    """Unconstrained generation — the benchmark's raw baseline."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.get_input_embeddings().weight.device)
    output = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)


def load_outlines_model(
    model_id: str = DEFAULT_MODEL_ID, *, token: str | None = None
) -> Any:
    """Load N-ATLAS as an Outlines model (optional alternative backend; needs Rust).

    Only used with :class:`~gyara.structured.OutlinesBackend`; prefer
    :func:`load_natlas` with :class:`~gyara.structured.TransformersJsonBackend`.
    """
    import outlines

    auth = resolve_token(token)
    return outlines.models.transformers(
        model_id,
        model_kwargs={"token": auth, "device_map": "auto", "torch_dtype": "float16"},
        tokenizer_kwargs={"token": auth},
    )
