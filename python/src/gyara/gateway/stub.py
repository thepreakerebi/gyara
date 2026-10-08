"""Run a stub Gyara Gateway (no model) for client development and e2e tests.

Serves the real Gateway app over a :class:`~gyara.structured.StubBackend`, so the SDKs
can be exercised end to end without a GPU. Configure via environment variables:

- ``GYARA_STUB_RESPONSE``: JSON returned for every request (omit to synthesise a
  minimal object that satisfies the request's schema).
- ``GYARA_STUB_PORT``: port to serve on (default 8744).
- ``GYARA_API_KEY``: if set, require ``Authorization: Bearer <key>``.

Run with ``python -m gyara.gateway.stub``.
"""

from __future__ import annotations

import json
import os


def main() -> None:
    import uvicorn

    from ..structured import StubBackend
    from .app import create_app

    raw = os.environ.get("GYARA_STUB_RESPONSE")
    response = json.loads(raw) if raw else None
    port = int(os.environ.get("GYARA_STUB_PORT", "8744"))
    app = create_app(StubBackend(response), api_key=os.environ.get("GYARA_API_KEY"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
