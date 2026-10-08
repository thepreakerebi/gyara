# Gyara

**A reliability layer for [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS), Nigeria's
sovereign LLM — so developers can ship real products on it.**

*Gyara* is Hausa for *to fix, to put right*. It cleans what goes into the model and
guarantees what comes out.

Built for the National AI Innovation Challenge (NAIC) 2026 — Problem Statement 01,
Developer Infrastructure.

## Why

N-ATLAS is open and downloadable, but it isn't yet something you can build a reliable
product on: there's no hosted API, the 8,092-token context fills fast because the
Llama-3 tokenizer fragments Nigerian languages, structured output is unreliable on an
8B model, and typed input usually arrives without diacritics. Gyara closes that gap.

## Two pillars

| Pillar | What it guarantees | Status |
| --- | --- | --- |
| **1 — Structured output** | Schema-valid JSON and tool-calls, by construction (constrained decoding) | Planned |
| **2 — Language normalization** | Clean Nigerian-language input + honest token budgeting for the 8k window | **Available** |

## Packages

- [`python/`](./python) — the Python SDK. Pillar 2 ships today (pure stdlib).
- `typescript/` — the TypeScript SDK (typed client + client-side normalizer). _Coming._
- `gateway/` — the OpenAI-compatible proxy that does constrained decoding server-side.
  _Coming._

## Architecture

```
Your app ──▶ Gyara (normalize in) ──▶ N-ATLAS ──▶ Gyara (constrain out) ──▶ valid response
```

Both SDKs talk to the **Gyara Gateway**, which runs the constrained decoding where the
model lives. The Python SDK can also run embedded, in-process with the model.

## License

Apache-2.0. Gyara is a tool for N-ATLAS, not a derivative of the model. N-ATLAS is an
initiative of the Federal Ministry of Communications, Innovation and Digital Economy,
powered by Awarri Technologies.
