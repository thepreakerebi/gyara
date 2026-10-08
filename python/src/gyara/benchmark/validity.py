"""The JSON-validity benchmark: raw prompting vs Gyara-constrained output.

The headline number for Pillar 1: what share of a task set yields valid, schema-
conforming JSON. Both measurement functions take injected callables, so the harness
is fully tested locally; the live model is plugged in on a GPU host.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..structured.schema import SchemaError, to_json_schema, validate

__all__ = ["BenchmarkResult", "parses_as", "run_raw", "run_gyara"]

Task = tuple[str, str, dict]
RawGenerate = Callable[[str, dict], str]


@dataclass(frozen=True)
class BenchmarkResult:
    """Outcome of a benchmark run."""

    total: int
    valid: int
    failures: tuple[str, ...] = ()

    @property
    def rate(self) -> float:
        """Share of tasks that produced valid, schema-conforming JSON."""
        return self.valid / self.total if self.total else 0.0


def parses_as(text: str, schema: dict) -> bool:
    """Whether ``text`` parses as JSON that conforms to ``schema``."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return False
    try:
        validate(data, schema)
    except SchemaError:
        return False
    return True


def run_raw(tasks: Iterable[Task], raw_generate: RawGenerate) -> BenchmarkResult:
    """Baseline: prompt the model, then try to parse its raw text as valid JSON."""
    total = valid = 0
    failures: list[str] = []
    for name, prompt, schema in tasks:
        total += 1
        json_schema = to_json_schema(schema)
        text = raw_generate(prompt, json_schema)
        if parses_as(text, json_schema):
            valid += 1
        else:
            failures.append(name)
    return BenchmarkResult(total, valid, tuple(failures))


def run_gyara(tasks: Iterable[Task], client) -> BenchmarkResult:
    """Gyara: structured output that validates internally; count any failures."""
    total = valid = 0
    failures: list[str] = []
    for name, prompt, schema in tasks:
        total += 1
        try:
            client.generate(prompt, schema)
            valid += 1
        except Exception:  # noqa: BLE001 - a failure here is a benchmark data point
            failures.append(name)
    return BenchmarkResult(total, valid, tuple(failures))
