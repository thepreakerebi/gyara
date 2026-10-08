"""Run the Gyara JSON-validity benchmark on the live N-ATLAS model.

Entry point for a Colab/Kaggle GPU notebook: ``from gyara.benchmark.run import main``.
It loads N-ATLAS once, then compares a raw-JSON baseline against Gyara's guided,
validated output. Lives in the package (not a fetched script) so a notebook always
runs the installed version, with no CDN caching.

Needs a GPU and the gated weights, so it is not part of the local test suite; the
harness and extraction logic it calls are unit-tested.
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


def _raw_prompt(prompt: str, schema: dict) -> str:
    return f"{prompt}\nReturn only a JSON object matching: {schema}"


def main() -> None:
    load_token()

    from gyara.benchmark import TASKS, run_raw
    from gyara.runtime import load_natlas, raw_generate
    from gyara.structured import PromptedJsonBackend, Structured

    print(f"Loading N-ATLAS once ({len(TASKS)} tasks)...")
    model, tokenizer = load_natlas()
    backend = PromptedJsonBackend(model, tokenizer)
    client = Structured(backend)

    def raw_fn(prompt: str, schema: dict) -> str:
        return raw_generate(model, tokenizer, _raw_prompt(prompt, schema))

    print("\nPhase 1/2 - raw N-ATLAS baseline (strict json.loads of the output)")
    raw = run_raw(TASKS, raw_fn)
    print(f"RAW    valid {raw.valid}/{raw.total} ({raw.rate:.0%})  failures={list(raw.failures)}")

    # Print the raw model text and the final result per task, to verify content.
    print("\nPhase 2/2 - Gyara structured output (raw model text + extracted result)")
    valid = 0
    for name, prompt, schema in TASKS:
        raw = backend.raw_completion(prompt, schema)
        print(f"  [{name}] raw: {raw[:200]!r}")
        try:
            result = client.generate(prompt, schema)
            print(f"  [{name}] -> {result}")
            valid += 1
        except Exception as exc:  # noqa: BLE001 - surface the real error per task
            print(f"  [{name}] -> FAILED {exc!r}")
    print(f"GYARA  valid {valid}/{len(TASKS)} ({valid / len(TASKS):.0%})")


if __name__ == "__main__":
    main()
