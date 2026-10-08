# Running Gyara on N-ATLAS (Kaggle)

The constrained-decoding backend and the JSON-validity benchmark need a GPU and the
gated N-ATLAS weights. This runs them on Kaggle's free GPU.

## Before you start

1. Accept the N-ATLaS licence: <https://huggingface.co/NCAIR1/N-ATLaS> (sign in → Agree).
2. Create a Hugging Face **read** token: <https://huggingface.co/settings/tokens>.

## Set up the notebook

1. New Kaggle Notebook → **Settings**:
   - **Accelerator:** GPU T4 (or 2×T4).
   - **Internet:** On.
2. **Add-ons → Secrets:** add a secret named `HF_TOKEN` with your token. Do not paste
   the token into a cell.

## Install Gyara

The repo is public. Clone then install from the local path — this avoids shell
quoting pitfalls (`#` and `[]`), and Kaggle already ships torch + transformers:

```python
!git clone -q https://github.com/thepreakerebi/gyara.git
!pip install -q ./gyara/python outlines==0.1.14 jsonschema pydantic
```

## Run the benchmark

Paste the contents of [`kaggle_run.py`](./kaggle_run.py) into a cell and call it:

```python
main()
```

Expected output — two lines, the headline numbers for Pillar 1:

```
RAW    valid  N/8 (xx%)  failures=[...]
GYARA  valid  8/8 (100%) failures=[]
```

`GYARA` is valid by construction; `RAW` is the base model prompted for JSON. The gap
is the benchmark result. Record both numbers and screenshot this cell for the demo.

## Notes

- Phase 1 loads the raw model, measures the baseline, then frees GPU memory before
  phase 2 loads the constrained model — so both fit on one T4.
- Pin `outlines==0.1.14` (the `outlines.generate.json` API this code targets).
