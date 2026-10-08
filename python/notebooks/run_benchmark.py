"""Run the Gyara JSON-validity benchmark on the live N-ATLAS model.

Designed for a Colab or Kaggle GPU notebook (see notebooks/README.md). It loads
N-ATLAS for the raw baseline, frees it, then loads the constrained Outlines model.

This script needs a GPU and the gated weights; it is intentionally not part of the
local test suite. The harness logic it calls (`gyara.benchmark`) is unit-tested.
"""

from __future__ import annotations

import os


def load_token() -> None:
    """Populate HF_TOKEN from Colab or Kaggle secrets, if not already in the env."""
    if os.environ.get("HF_TOKEN"):
        return
    try:  # Colab
        from google.colab import userdata

        os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
        return
    except Exception:  # noqa: BLE001 - not on Colab
        pass
    try:  # Kaggle
        from kaggle_secrets import UserSecretsClient

        os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
        return
    except Exception:  # noqa: BLE001 - not on Kaggle
        pass
    print("No Colab/Kaggle secret found; relying on the HF_TOKEN env var.")


def main() -> None:
    load_token()

    from gyara.benchmark import TASKS, run_gyara, run_raw
    from gyara.runtime import load_natlas, raw_generate
    from gyara.structured import Structured, TransformersJsonBackend

    print(f"Loading N-ATLAS once ({len(TASKS)} tasks)...")
    model, tokenizer = load_natlas()

    print("Phase 1/2 - raw N-ATLAS baseline")
    raw = run_raw(
        TASKS,
        lambda prompt, schema: raw_generate(
            model, tokenizer, f"{prompt}\nReturn only a JSON object matching: {schema}"
        ),
    )
    print(f"RAW    valid {raw.valid}/{raw.total} ({raw.rate:.0%})  failures={list(raw.failures)}")

    print("Phase 2/2 - Gyara constrained output")
    client = Structured(TransformersJsonBackend(model, tokenizer))
    gyara = run_gyara(TASKS, client)
    print(
        f"GYARA  valid {gyara.valid}/{gyara.total} "
        f"({gyara.rate:.0%})  failures={list(gyara.failures)}"
    )


if __name__ == "__main__":
    main()
