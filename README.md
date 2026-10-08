# Gyara

**A reliability layer for [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS), Nigeria's
sovereign LLM — so developers can ship real products on it.**

*Gyara* is Hausa for *to fix, to put right*. It cleans what goes into the model and
guarantees what comes out: valid, schema-conforming structured data, and clean
Nigerian-language input. One `pip install` (Python), one `npm i` (TypeScript), or a
self-hosted HTTP gateway.

Built for the National AI Innovation Challenge (NAIC) 2026 — Developer Infrastructure.

---

## Why Gyara exists

N-ATLAS is open and downloadable, but it isn't yet something you can build a reliable
product on:

- **No hosted API** — every team self-hosts the 8B and re-writes the same serving glue.
- **Unreliable structured output** — an 8B model wraps answers in ```json fences, echoes
  the JSON schema instead of answering, and sometimes degenerates, so an app that needs
  a record back gets unparseable text.
- **A tiny, fragmented context** — the 8,092-token window fills fast because the Llama-3
  tokenizer splits Yoruba, Hausa and Igbo into far more tokens per word than English.
- **Raw local-language input** — diacritics usually arrive missing, which degrades output.

Gyara closes that gap, operating directly on the model rather than around it.

## The two pillars

| Pillar | What it does | Status |
| --- | --- | --- |
| **1 — Structured output** (`gyara.structured`) | Schema-valid JSON and tool-calling: guide the model to JSON, extract the object from fenced/rambling output, validate it, and repair on a miss. Constrained-decoding backends available where their deps install. | ✅ |
| **2 — Language normalization** (`gyara.normalize`) | Unicode NFC, diacritic restoration, and a tokenizer-aware budget for the 8,092-token window. Pure stdlib, no GPU. | ✅ |

## Result on the live model

An 8-task extraction benchmark (English, Nigerian Pidgin, Yoruba) on N-ATLAS 8B:

| | Valid, schema-conforming records |
| --- | --- |
| **Raw** — `json.loads` of the model's output | **0 / 8** |
| **Gyara** — guide → extract → validate → repair | **8 / 8** |

Same model, same prompts; the only difference is Gyara. It recovers the correct record
even from the Yoruba sentence, and even when the model emits the JSON schema instead of
the answer. Reproduce it on a Kaggle GPU notebook —
[`python/notebooks/README.md`](./python/notebooks/README.md).

## How it integrates with N-ATLAS

This is why a general-purpose wrapper can't stand in — Gyara works *on* the model:

- formats every prompt with N-ATLAS's **own chat template** (without it the 8B echoes
  the prompt and degenerates);
- tames its decoding (`repetition_penalty`) to stop runaway repetition;
- works within the published **8,092-token** context, measuring the true token cost of
  Nigerian-language text;
- recovers structure from N-ATLAS's specific output quirks (code fences, schema echoes).

---

## Architecture

```
app / SDK ──► Gyara ──► N-ATLAS (8B) ──► Gyara ──► valid record
              in:  normalize NG-language input, budget the 8,092-token window
              out: guide to JSON, extract the object, validate, repair
```

Both SDKs can call the **Gyara Gateway** (an HTTP proxy that runs the generation
server-side), and the Python SDK can also run embedded, in-process with the model.

## Packages

| Path | What it is |
| --- | --- |
| [`python/`](./python) | Python SDK — both pillars, the model runtime, the benchmark, and the Gateway. |
| [`typescript/`](./typescript) | TypeScript SDK for Node and the browser — typed client, Zod → JSON Schema, client-side normalizer. |
| [`python/src/gyara/gateway`](./python/src/gyara/gateway) | FastAPI proxy (`POST /v1/structured`) both SDKs and any app call. |

---

## Quick start — Python

```bash
pip install ./python          # or: pip install "gyara @ git+https://github.com/thepreakerebi/gyara#subdirectory=python"
```

**Structured output** (Pillar 1):

```python
from pydantic import BaseModel
from gyara.structured import Structured, PromptedJsonBackend

class Transfer(BaseModel):
    recipient: str
    amount_naira: int

# `backend` wraps a loaded N-ATLAS (see gyara.runtime.load_natlas), or use StubBackend in tests.
client = Structured(PromptedJsonBackend(model, tokenizer))
record = client.generate("Send 2k to Ada", schema=Transfer)
# -> {"recipient": "Ada", "amount_naira": 2000}  — validated, never half-parsed text
```

**Normalization** (Pillar 2, no GPU):

```python
from gyara.normalize import normalize_text, DictionaryRestorer, TokenBudget

text = normalize_text("Báwo  ni​\n\n\n\nse  wa?")        # NFC, zero-width, whitespace
text = DictionaryRestorer({"omo": "ọmọ"}).restore("Awon omo") # -> "Awon ọmọ"

budget = TokenBudget(encode=tokenizer.encode)                 # true cost in the 8,092 window
if not budget.fits(text, reserved=512):
    text = budget.truncate(text)
```

## Quick start — TypeScript

```bash
npm install gyara zod
```

```ts
import { z } from "zod";
import { Structured, GatewayBackend, normalizeText } from "gyara";

const client = new Structured(new GatewayBackend("https://your-gateway/v1/structured"));
const Transfer = z.object({ recipient: z.string(), amount_naira: z.number().int() });
const record = await client.generate("Send 2k to Ada", Transfer);
```

## Quick start — Gateway

```bash
# Serve the live model (GPU host):
python -m gyara.gateway.server
# Or a GPU-free stub for client development:
python -m gyara.gateway.stub
```

```
POST /v1/structured   { "prompt": "...", "schema": { ... } }  ->  { "data": { ... } }
GET  /health
```

Set `GYARA_API_KEY` to require `Authorization: Bearer <key>`.

---

## Verify it yourself

```bash
# Python SDK, Gateway, benchmark harness — 78 tests
cd python && uv venv && uv pip install -e ".[dev]" && uv run pytest

# TypeScript SDK — 46 unit tests
cd typescript && npm install && npm test

# Cross-language: the TS client against the real Python Gateway (no GPU) — 2 tests
cd typescript && npm run test:e2e
```

## Repository layout

```
gyara/
├── python/
│   ├── src/gyara/
│   │   ├── normalize/      # Pillar 2: text, diacritics, token budget
│   │   ├── structured/     # Pillar 1: schema, tools, backends, client
│   │   ├── gateway/        # FastAPI proxy + stub + server
│   │   ├── benchmark/      # tasks, validity harness, run.main
│   │   └── runtime.py      # load N-ATLAS, chat-template generation (GPU host)
│   ├── notebooks/          # how to reproduce the benchmark on Kaggle/Colab
│   └── tests/
└── typescript/
    ├── src/{normalize,structured}/
    └── e2e/                # TS client <-> live Python gateway
```

## Honest notes

- The benchmark measures **validity** (schema-conformance): a true 8/8. Content
  correctness is ~7/8 — the model misread one amount ("5k" → 50000), which Gyara
  structured faithfully. Gyara guarantees the record's shape, not the model's reading.
- Gyara is pick-and-shovel infrastructure, and N-ATLAS's licence is non-commercial with
  a 1,000-user cap — an ecosystem and research contribution rather than a product.

## License

Apache-2.0. Gyara is a tool for N-ATLAS, not a derivative of the model. N-ATLAS is an
initiative of the Federal Ministry of Communications, Innovation and Digital Economy,
powered by Awarri Technologies.
