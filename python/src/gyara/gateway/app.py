"""The Gyara Gateway: an HTTP proxy for structured output over any backend.

Both SDKs (and any existing app) can POST a prompt and a JSON schema here and get a
validated object back. The constrained/guided generation runs server-side, so clients
stay thin. The app is built from an injected backend, so it is tested with
``StubBackend`` and served against the live model via :mod:`gyara.gateway.server`.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ..structured import SchemaError, Structured, StructuredBackend

__all__ = ["create_app", "StructuredRequest", "StructuredResponse"]


class StructuredRequest(BaseModel):
    prompt: str
    # Named json_schema internally to avoid shadowing BaseModel.schema; accepts "schema".
    json_schema: dict[str, Any] = Field(alias="schema")

    model_config = {"populate_by_name": True}


class StructuredResponse(BaseModel):
    data: Any


def create_app(backend: StructuredBackend, *, api_key: str | None = None) -> FastAPI:
    """Build the Gateway app over ``backend``.

    Args:
        backend: Any :class:`~gyara.structured.StructuredBackend`.
        api_key: If set (or ``GYARA_API_KEY`` is in the env), requests must send
            ``Authorization: Bearer <key>``.
    """
    app = FastAPI(title="Gyara Gateway", version="0.1.0")
    client = Structured(backend)
    required_key = api_key if api_key is not None else os.environ.get("GYARA_API_KEY")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/structured", response_model=StructuredResponse)
    def structured(
        request: StructuredRequest, authorization: str | None = Header(default=None)
    ) -> StructuredResponse:
        if required_key:
            token = (authorization or "").removeprefix("Bearer ").strip()
            if token != required_key:
                raise HTTPException(status_code=401, detail="invalid or missing API key")
        try:
            data = client.generate(request.prompt, request.json_schema)
        except SchemaError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return StructuredResponse(data=data)

    return app
