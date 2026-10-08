"""Tests for the dependency-free extraction used by PromptedJsonBackend."""

import pytest

from gyara.structured import extract_json, extract_json_candidates


def test_extracts_plain_object():
    assert extract_json('{"recipient": "Chidi", "amount_naira": 5000}') == {
        "recipient": "Chidi",
        "amount_naira": 5000,
    }


def test_extracts_from_code_fence_and_prose():
    # The exact shape N-ATLAS produced: a leading colon, a ```json fence, then rambling.
    raw = (
        ':\n```json\n{\n "recipient": "Chidi",\n "amount_naira": 5000\n}\n```\n'
        '```json\n{"type": "object"}'
    )
    assert extract_json(raw) == {"recipient": "Chidi", "amount_naira": 5000}


def test_candidates_returns_every_object_in_order():
    raw = '{"label": "positive"} noise {"type": "object", "properties": {}}'
    candidates = extract_json_candidates(raw)
    assert candidates == [
        {"label": "positive"},
        {"type": "object", "properties": {}},
    ]


def test_candidates_let_a_later_valid_object_win():
    # The model echoes the schema first, then gives the real answer second.
    from gyara.structured import SchemaError, validate

    schema = {
        "type": "object",
        "properties": {"label": {"type": "string", "enum": ["positive", "negative"]}},
        "required": ["label"],
        "additionalProperties": False,
    }
    raw = '{"type": "object", "properties": {"label": {}}} then {"label": "positive"}'
    valid = None
    for candidate in extract_json_candidates(raw):
        try:
            validate(candidate, schema)
            valid = candidate
            break
        except SchemaError:
            continue
    assert valid == {"label": "positive"}


def test_no_object_found():
    assert extract_json_candidates("no json here") == []
    with pytest.raises(ValueError):
        extract_json("no json here")
