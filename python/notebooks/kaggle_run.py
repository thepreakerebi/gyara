"""Run the Gyara JSON-validity benchmark on the live N-ATLAS model.

Designed for a Kaggle GPU notebook (see notebooks/README.md). It loads N-ATLAS once
for the raw baseline, frees it, then loads the constrained Outlines model — so both
phases fit on a single 16 GB T4.

This script needs a GPU and the gated weights; it is intentionally not part of the
local test suite. The harness logic it calls (`gyara.benchmark`) is unit-tested.
"""

from __future__ import annotations

import gc
import os


def load_token() -> None:
    """Populate HF_TOKEN from a Kaggle Secret if it isn't already in the environment."""
    if os.environ.get("HF_TOKEN"):
        return
    try:
        from kaggle_secrets import UserSecretsClient

        os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
    except Exception as exc:  # noqa: BLE001 - optional on non-Kaggle hosts
        print(f"No Kaggle secret ({exc}); relying on HF_TOKEN env var.")


def run_raw_phase() -> None:
    from gyara.benchmark import TASKS, run_raw
    from gyara.runtime import load_text_generator

    generate = load_text_generator()

    def raw_generate(prompt: str, schema: dict) -> str:
        instruction = (
            f"{prompt}\nReturn ONLY a JSON object matching this schema:\n{schema}"
        )
        return generate(instruction, 256)

    result = run_raw(TASKS, raw_generate)
    print(
        f"RAW    valid {result.valid}/{result.total} "
        f"({result.rate:.0%})  failures={list(result.failures)}"
    )


def run_gyara_phase() -> None:
    from gyara.benchmark import TASKS, run_gyara
    from gyara.runtime import load_outlines_model
    from gyara.structured import OutlinesBackend, Structured

    client = Structured(OutlinesBackend(load_outlines_model()))
    result = run_gyara(TASKS, client)
    print(
        f"GYARA  valid {result.valid}/{result.total} "
        f"({result.rate:.0%})  failures={list(result.failures)}"
    )


def free_gpu() -> None:
    gc.collect()
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:  # noqa: BLE001
        pass


def main() -> None:
    load_token()
    print("Phase 1/2 — raw N-ATLAS baseline")
    run_raw_phase()
    free_gpu()
    print("Phase 2/2 — Gyara constrained output")
    run_gyara_phase()


if __name__ == "__main__":
    main()
