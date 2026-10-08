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

The repo is private, so install with a GitHub token (store it as a second Kaggle
secret `GH_TOKEN`), or make the repo public first. In a cell:

```python
import os
from kaggle_secrets import UserSecretsClient
gh = UserSecretsClient().get_secret("GH_TOKEN")
url = f"git+https://{gh}@github.com/thepreakerebi/gyara.git#subdirectory=python"
!pip install -q "gyara[model] @ {url}" "outlines==0.1.14"
```

(If the repo is public, drop `GH_TOKEN` and use the plain URL.)

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
