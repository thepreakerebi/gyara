# Running Gyara on N-ATLAS (Colab or Kaggle)

The constrained-decoding backend and the JSON-validity benchmark need a GPU and the
gated N-ATLAS weights. The default backend uses `lm-format-enforcer` (pure Python, no
Rust toolchain), so it installs cleanly on both Colab and Kaggle images.

## Before you start

1. Accept the N-ATLaS licence: <https://huggingface.co/NCAIR1/N-ATLaS> (sign in → Agree).
2. Create a Hugging Face **read** token: <https://huggingface.co/settings/tokens>.

## Google Colab (recommended)

1. New notebook → **Runtime → Change runtime type → T4 GPU**.
2. Secrets (the 🔑 icon, left sidebar) → add `HF_TOKEN` with your token, toggle
   **Notebook access** on. Don't paste the token into a cell.
3. Cell 1 — install (clone into `gyara_src`, not `gyara`, to avoid shadowing the package):

   ```python
   !git clone -q https://github.com/thepreakerebi/gyara.git gyara_src
   !pip install -q ./gyara_src/python lm-format-enforcer jsonschema pydantic bitsandbytes
   ```

4. Cell 2 — run (imports from the installed package, so it is always current):

   ```python
   from gyara.benchmark.run import main
   main()
   ```

## Kaggle (alternative)

Same two cells, but add the secret under **Add-ons → Secrets** (`HF_TOKEN`), and set
**Settings → Accelerator → GPU T4 ×2** with Internet on. If `outlines` fails to build
on Kaggle, use Colab.

## Expected output

```
RAW    valid N/8 (xx%)  failures=[...]
GYARA  valid 8/8 (100%) failures=[]
```

`GYARA` is valid by construction; `RAW` is the base model prompted for JSON. The gap
is the benchmark result. Screenshot this cell for the demo.

## Share a hosted gateway (let others test on the live model, no GPU for them)

Run the Gateway behind a public Cloudflare tunnel so developers can call the real
N-ATLAS endpoint over HTTP from anywhere. Use the same GPU setup as above, then one cell:

```python
# 1. Install (clone into gyara_src, add the gateway deps)
!rm -rf gyara_src && git clone -q https://github.com/thepreakerebi/gyara.git gyara_src
!pip install -q --force-reinstall --no-deps ./gyara_src/python
!pip install -q jsonschema pydantic fastapi uvicorn

# 2. Reload the fresh package, set a shared secret, and open the tunnel
import sys, importlib, os
for _m in [m for m in list(sys.modules) if m == "gyara" or m.startswith("gyara.")]:
    del sys.modules[_m]
importlib.invalidate_caches()
os.environ["GYARA_API_KEY"] = "pick-a-shared-secret"   # only holders of this key can call it
from gyara.gateway.tunnel import main
main()
```

It prints a public URL like `https://something.trycloudflare.com`. **Keep the cell
running** — the endpoint is live only while the notebook session is. Share:

- Endpoint: `https://<url>/v1/structured`
- Header: `Authorization: Bearer pick-a-shared-secret`

Your testers then point an SDK at it with no GPU or Hugging Face access of their own:

```ts
import { z } from "zod";
import { Structured, GatewayBackend } from "gyara";
const client = new Structured(
  new GatewayBackend("https://<url>/v1/structured", { apiKey: "pick-a-shared-secret" }),
);
await client.generate("Send 2k to Ada", z.object({ recipient: z.string(), amount_naira: z.number().int() }));
```

Or plain `curl`:

```bash
curl -X POST "https://<url>/v1/structured" \
  -H "Authorization: Bearer pick-a-shared-secret" -H "content-type: application/json" \
  -d '{"prompt":"Send 2k to Ada","schema":{"type":"object","properties":{"recipient":{"type":"string"},"amount_naira":{"type":"integer"}},"required":["recipient","amount_naira"]}}'
```

Set a non-trivial `GYARA_API_KEY` — the tunnel URL is public, and the key is the only
thing gating access to your running model.
