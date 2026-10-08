import unicodedata

import pytest

from gyara.normalize import normalize_text, strip_diacritics


def test_collapses_horizontal_whitespace_but_keeps_paragraphs():
    raw = "Bawo   ni\t\tani?\n\n\n\nMo wa daadaa  "
    assert normalize_text(raw) == "Bawo ni ani?\n\nMo wa daadaa"


def test_strips_zero_width_characters():
    raw = "o​mo﻿"
    assert normalize_text(raw) == "omo"


def test_nfc_composes_combining_marks():
    # "ọ" typed as base o + combining dot below should compose to one code point.
    decomposed = "ọ"
    out = normalize_text(decomposed)
    assert out == unicodedata.normalize("NFC", decomposed)
    assert len(out) == 1


def test_strip_diacritics_reduces_to_ascii_base():
    assert strip_diacritics("Yorùbá") == "Yoruba"
    assert strip_diacritics("ọmọ") == "omo"
    assert strip_diacritics("Ṣàngó") == "Sango"


def test_invalid_form_rejected():
    with pytest.raises(ValueError):
        normalize_text("x", form="NFG")


def test_non_string_rejected():
    with pytest.raises(TypeError):
        normalize_text(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        strip_diacritics(None)  # type: ignore[arg-type]
