"""Tests for the pure parsing helper of the Transformers backend (no model/GPU)."""

import pytest

from gyara.structured import first_json_object


def test_parses_clean_object():
    assert first_json_object('{"name": "Ada", "amount": 10}') == {"name": "Ada", "amount": 10}


def test_ignores_trailing_tokens():
    # Constrained decoding can emit extra tokens after the object closes.
    assert first_json_object('{"label": "positive"}\n\nSure, done!') == {"label": "positive"}


def test_tolerates_leading_whitespace():
    assert first_json_object('   \n {"x": 1}') == {"x": 1}


def test_raises_on_non_json():
    with pytest.raises(ValueError):
        first_json_object("Sure! Here is the info you asked for.")
