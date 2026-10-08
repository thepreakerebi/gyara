"""Serve the Gyara Gateway against the live N-ATLAS model (GPU host only).

Loads N-ATLAS once, wraps it in the guided-JSON backend, and runs the app with
uvicorn. Not part of the local test suite (needs a GPU); the app itself is tested in
:mod:`tests.test_gateway` with a stub backend.
"""

from __future__ import annotations


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Load N-ATLAS and serve the Gateway on ``host:port``."""
    import uvicorn

    from ..runtime import load_dotenv, load_natlas
    from ..structured import PromptedJsonBackend
    from .app import create_app

    load_dotenv()
    model, tokenizer = load_natlas()
    app = create_app(PromptedJsonBackend(model, tokenizer))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
