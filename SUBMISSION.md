# Gyara — overview for reviewers

Gyara is a reliability layer that makes [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS),
Nigeria's sovereign LLM, safe to build real products on. N-ATLAS produces the right
content but wraps it in ```json fences and often echoes the schema itself, so an app
that needs structured data gets nothing usable from raw output. Gyara fixes that, in
one `pip install` (Python), one `npm i` (TypeScript), or a self-hosted HTTP gateway.

This page is a map of the work and how to check it yourself. Full detail is in the
[README](./README.md) and the per-package docs.

## The result

An 8-task extraction benchmark (English, Nigerian Pidgin, Yoruba) on the live N-ATLAS 8B:

| | Valid, schema-conforming records |
| --- | --- |
| Raw — `json.loads` of the model's output | **0 / 8** |
| Gyara — guide → extract → validate → repair | **8 / 8** |

Same model, same prompts; the only difference is Gyara. It recovers the correct record
even from the Yoruba sentence and even when the model emits the JSON schema instead of
the answer.

## How it integrates with N-ATLAS

Gyara operates *on* the model, which is why a general-purpose wrapper cannot stand in:

- formats every prompt with N-ATLAS's **own chat template** — without it the 8B echoes
  the prompt and degenerates;
- tames its decoding (`repetition_penalty`) to stop runaway repetition;
- works within its published **8,092-token** context, measuring the true cost of
  Nigerian-language text (which the Llama-3 tokenizer fragments);
- recovers structure from N-ATLAS's specific output quirks (code fences, schema echoes).

## How to verify it yourself

```bash
# Python SDK, Gateway, benchmark harness — 78 tests
cd python && uv venv && uv pip install -e ".[dev]" && uv run pytest

# TypeScript SDK — 46 tests
cd typescript && npm install && npm test

# Cross-language: the TS client against the real Python Gateway (no GPU)
cd typescript && npm run test:e2e
```

Reproduce the headline result on the live model from a Kaggle GPU notebook — steps in
[`python/notebooks/README.md`](./python/notebooks/README.md). It prints `RAW 0/8` and
`GYARA 8/8` and the raw model output for each task, so the comparison is inspectable.

Try the SDKs against a GPU-free stub of the real gateway:

```bash
python -m gyara.gateway.stub          # serves POST /v1/structured
```

## Architecture

```
app / SDK ──► Gyara ──► N-ATLAS (8B) ──► Gyara ──► valid record
              in:  normalize NG-language input, budget the 8,092-token window
              out: guide to JSON, extract the object, validate, repair
```

- `gyara.normalize` (pure stdlib): Unicode NFC, diacritic restoration, tokenizer-aware
  context budget.
- `gyara.structured`: schema handling, tool-calling, and backends. `PromptedJsonBackend`
  (transformers only) powers the result above; `OutlinesBackend` /
  `TransformersJsonBackend` offer true constrained decoding where their deps install.
- `gyara.gateway`: a FastAPI proxy (`POST /v1/structured`) both SDKs and any app call.

## Honest notes

- The benchmark measures **validity** (schema-conformance): a true 8/8. Content
  correctness is ~7/8 — the model misread one amount ("5k" → 50000), which Gyara
  structured faithfully. Gyara guarantees the record's shape, not the model's reading.
- Gyara is pick-and-shovel infrastructure, and N-ATLAS's licence is non-commercial with
  a 1,000-user cap — an ecosystem and research contribution rather than a product.
