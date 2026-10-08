# gyara (TypeScript)

A reliability layer for [N-ATLAS](https://huggingface.co/NCAIR1/N-ATLaS), Nigeria's
sovereign LLM — for Node and the browser. Part of the [Gyara](../README.md) monorepo;
mirrors the [Python SDK](../python).

## Install

```bash
npm install gyara
# zod is an optional peer dep if you want to define schemas with it
npm install zod
```

## Pillar 1 — guaranteed structured output

```ts
import { z } from "zod";
import { Structured, GatewayBackend, Tool } from "gyara";

// Point at the Gyara Gateway (constrained decoding runs server-side on N-ATLAS).
const client = new Structured(new GatewayBackend("https://your-gateway/v1"));

const Transfer = z.object({ name: z.string(), amount: z.number().int() });
const data = await client.generate("Send 5k to Chidi for market", Transfer);
// -> { name: "Chidi", amount: 5000 }, validated — never half-parsed text

const send = new Tool("send_money", "Send money to a contact", {
  type: "object",
  properties: { to: { type: "string" }, amount: { type: "integer" } },
  required: ["to", "amount"],
});
const call = await client.callTool("Pay Ada 10", [send]); // -> { name, arguments }
```

Use `StubBackend` for tests and local dev — no server, no GPU.

## Pillar 2 — Nigerian-language normalization

```ts
import { normalizeText, DictionaryRestorer, TokenBudget } from "gyara";

const text = normalizeText("Báwo  ni​\n\n\n\nse  wa?");
const restored = new DictionaryRestorer({ omo: "ọmọ" }).restore("Awon omo"); // "Awon ọmọ"

// Fit to N-ATLAS's 8,092-token window with any tokenizer (inject its encode).
const budget = new TokenBudget((t) => tokenizer.encode(t));
if (!budget.fits(text, 512)) console.warn(budget.report(text));
```

## Develop

```bash
npm install
npm run typecheck
npm test
npm run build
```

## License

Apache-2.0. Gyara is a tool for N-ATLAS, not a derivative of the model.
