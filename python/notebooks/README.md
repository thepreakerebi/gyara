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
