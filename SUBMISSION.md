# Gyara — NAIC 2026 Submission

**Problem Statement 01 — Developer Infrastructure** · Track B (Innovation & Enterprise)

Gyara is a reliability layer that makes [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS),
Nigeria's sovereign LLM, safe to build real products on. N-ATLAS reliably produces the
right content but wraps it in ```json fences and often echoes the schema itself, so an
app that needs structured data gets nothing usable from raw output. Gyara fixes that.

## Result (measured on the live model)

An 8-task extraction benchmark (English, Nigerian Pidgin, Yoruba) on N-ATLAS 8B:

| | Valid, schema-conforming records |
| --- | --- |
| **Raw** — `json.loads` of the model's output | **0 / 8** |
| **Gyara** — guide → extract → validate → repair | **8 / 8** |

Same model, same prompts; the only difference is Gyara. It recovers the correct record
even from the Yoruba sentence and even when the model emits the JSON schema instead of
the answer. Gyara guarantees the *structure*; content tracks the model's own accuracy.

Reproduce it on a Kaggle GPU notebook — see [`python/notebooks/README.md`](./python/notebooks/README.md).

## Architecture

```
app / SDK ──► Gyara ──► N-ATLAS (8B) ──► Gyara ──► valid record
              in:  normalize NG-language input, budget the 8,092-token window
              out: guide to JSON, extract the object, validate, repair
```

- **Pillar 2 — normalization** (`gyara.normalize`, pure stdlib): Unicode NFC, diacritic
  restoration, and a tokenizer-aware budget for the 8,092-token context.
- **Pillar 1 — structured output** (`gyara.structured`): schema handling, tool-calling,
  and backends. The portable `PromptedJsonBackend` (transformers only) powers the result
  above; `OutlinesBackend` / `TransformersJsonBackend` offer true constrained decoding
  where their dependencies install.
- **Gateway** (`gyara.gateway`): a FastAPI proxy (`POST /v1/structured`) so the Python
  and TypeScript SDKs — and any app — call one endpoint; generation runs server-side.

## N-ATLAS integration (why this can't be faked)

Gyara operates *on* N-ATLAS directly: it formats prompts with the model's own chat
template (without which the 8B echoes and degenerates), tames its decoding
(`repetition_penalty`), works within its published 8,092-token limit, and recovers
structure from its specific output quirks. A GPT wrapper cannot stand in — the whole
value is lifting Nigeria's sovereign model from unusable raw output to validated data.

## Submission components

| Required | Where |
| --- | --- |
| Working artefact | This repo: `pip install ./python`, `npm i` in `typescript/`, Gateway app |
| N-ATLAS integration evidence | Benchmark run + `gyara.runtime` / backends (chat template, decoding, token budget) |
| Real-world validation | The 0/8 → 8/8 benchmark on the live model; + external developers running it |
| Technical documentation | [root README](./README.md), [python](./python/README.md), [typescript](./typescript/README.md), this file |
| Video demonstration | Screen-record the Kaggle run (raw 0/8 → Gyara 8/8) end to end |
| Team & endorsement | Two-person team; Track B under a registered CAC entity |

## Build & test

```bash
# Python
cd python && uv venv && uv pip install -e ".[dev]" && uv run pytest    # 77 tests

# TypeScript
cd typescript && npm install && npm test                               # 46 tests
```

## Honesty notes

- The benchmark measures **validity** (schema-conformance): a true 8/8. Content
  correctness is ~7/8 — the model misread one amount ("5k" → 50000), which Gyara
  structured faithfully. Gyara guarantees the record's shape, not the model's reading.
- Gyara is pick-and-shovel infrastructure, and N-ATLAS's licence is non-commercial with
  a 1,000-user cap — this is an ecosystem and research contribution, not a revenue play.
