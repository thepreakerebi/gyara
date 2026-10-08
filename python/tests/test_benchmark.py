"""Tests for the benchmark harness using fakes (no model)."""

import json

from gyara.benchmark import TASKS, BenchmarkResult, parses_as, run_gyara, run_raw
from gyara.structured import Structured, StubBackend

SCHEMA = {
    "type": "object",
    "properties": {"recipient": {"type": "string"}, "amount_naira": {"type": "integer"}},
    "required": ["recipient", "amount_naira"],
}
SAMPLE_TASKS = [
    ("good", "p1", SCHEMA),
    ("chatty", "p2", SCHEMA),
    ("broken", "p3", SCHEMA),
]


def test_parses_as():
    assert parses_as('{"recipient": "Ada", "amount_naira": 10}', SCHEMA)
    assert not parses_as("Sure! Here you go: ...", SCHEMA)  # not JSON
    assert not parses_as('{"recipient": "Ada"}', SCHEMA)  # missing required


def test_run_raw_counts_only_valid_json():
    def raw_generate(prompt, schema):
        if prompt == "p1":
            return '{"recipient": "Ada", "amount_naira": 10}'
        if prompt == "p2":
            return "Sure, here is the info you asked for."  # chatty, not JSON
        return '{"recipient": "Ada"}'  # missing required field

    result = run_raw(SAMPLE_TASKS, raw_generate)
    assert result.total == 3
    assert result.valid == 1
    assert set(result.failures) == {"chatty", "broken"}
    assert round(result.rate, 3) == round(1 / 3, 3)


def test_run_gyara_is_valid_by_construction():
    # A stub that returns a valid object (as the constrained backend would).
    client = Structured(StubBackend(response={"recipient": "Ada", "amount_naira": 10}))
    result = run_gyara(SAMPLE_TASKS, client)
    assert result.valid == 3
    assert result.rate == 1.0


def test_run_gyara_records_failures_when_backend_misbehaves():
    client = Structured(StubBackend(response={"recipient": "Ada"}))  # invalid
    result = run_gyara(SAMPLE_TASKS, client)
    assert result.valid == 0
    assert len(result.failures) == 3


def test_benchmark_result_rate_handles_empty():
    assert BenchmarkResult(0, 0).rate == 0.0


def test_shipped_task_set_is_wellformed():
    assert len(TASKS) >= 8
    for name, prompt, schema in TASKS:
        assert isinstance(name, str) and name
        assert isinstance(prompt, str) and prompt
        json.dumps(schema)  # schema must be JSON-serialisable
