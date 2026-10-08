# gyara (Python)

A reliability layer for [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS), Nigeria's
sovereign LLM. Gyara makes the model safe to build real products on.

This package is part of the [Gyara](../README.md) monorepo. The core normalization
module is pure stdlib — no runtime dependencies, no GPU.

## Install

```bash
pip install gyara
```

## Pillar 2 — Nigerian-language normalization & token budgeting

```python
from gyara.normalize import normalize_text, DictionaryRestorer, TokenBudget

# 1. Clean raw input: Unicode NFC, zero-width chars, whitespace.
text = normalize_text("Báwo  ni​\n\n\n\nse  wa?")

# 2. Restore missing diacritics (baseline dictionary restorer; learned model later).
restorer = DictionaryRestorer({"omo": "ọmọ", "yoruba": "Yorùbá"})
text = restorer.restore("Awon omo Yoruba")   # -> "Awon ọmọ Yorùbá"

# 3. Fit text to N-ATLAS's 8,092-token window using the real tokenizer.
#    `encode` is any str -> token-ids callable (inject the N-ATLAS tokenizer on a GPU host).
budget = TokenBudget(encode=tokenizer.encode)
if not budget.fits(text, reserved=512):       # leave room for the response
    text = budget.truncate(text)
report = budget.report(text)                  # tokens-per-word, per-char
```

## Develop

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run ruff check .
uv run pytest
```

## Roadmap

- **Pillar 1 — structured output:** schema-constrained `generate()` and `call_tool()`
  (runs where the model runs; see the monorepo roadmap).
- Learned diacritic restorer and curated Yoruba/Hausa lexicons.

## License

Apache-2.0. Gyara is a tool for N-ATLAS, not a derivative of the model.
