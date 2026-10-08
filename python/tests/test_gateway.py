"""Tests for the Gateway app using a stub backend (no model, no GPU)."""

from fastapi.testclient import TestClient

from gyara.gateway import create_app
from gyara.structured import StubBackend

SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
}


def make_client(response=None, **kwargs):
    return TestClient(create_app(StubBackend(response), **kwargs))


def test_health():
    assert make_client().get("/health").json() == {"status": "ok"}


def test_structured_returns_validated_data():
    client = make_client(response={"name": "Ada"})
    resp = client.post("/v1/structured", json={"prompt": "who?", "schema": SCHEMA})
    assert resp.status_code == 200
    assert resp.json() == {"data": {"name": "Ada"}}


def test_structured_rejects_invalid_output_with_422():
    client = make_client(response={})  # missing required "name"
    resp = client.post("/v1/structured", json={"prompt": "who?", "schema": SCHEMA})
    assert resp.status_code == 422


def test_missing_fields_are_422():
    resp = make_client().post("/v1/structured", json={"prompt": "who?"})
    assert resp.status_code == 422  # schema field required


class _FailingBackend:
    def generate_json(self, prompt, schema):
        raise RuntimeError("secret internal detail")


def test_internal_errors_are_not_leaked():
    client = TestClient(create_app(_FailingBackend()))
    resp = client.post("/v1/structured", json={"prompt": "x", "schema": SCHEMA})
    assert resp.status_code == 500
    assert "secret internal detail" not in resp.text
    assert resp.json()["detail"] == "generation failed"


def test_api_key_enforced_when_set():
    client = make_client(response={"name": "Ada"}, api_key="secret")
    body = {"prompt": "who?", "schema": SCHEMA}

    assert client.post("/v1/structured", json=body).status_code == 401
    ok = client.post(
        "/v1/structured", json=body, headers={"Authorization": "Bearer secret"}
    )
    assert ok.status_code == 200
    assert ok.json() == {"data": {"name": "Ada"}}
