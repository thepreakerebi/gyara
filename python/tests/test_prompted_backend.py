"""Tests for the dependency-free extraction used by PromptedJsonBackend."""

import pytest

from gyara.structured import extract_json


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


def test_takes_first_object_only():
    assert extract_json('{"label": "positive"} and then {"label": "negative"}') == {
        "label": "positive"
    }


def test_raises_when_no_object():
    with pytest.raises(ValueError):
        extract_json("Sure, here is the information you asked for.")
