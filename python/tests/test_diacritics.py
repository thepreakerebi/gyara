import pytest

from gyara.normalize import DictionaryRestorer, Restorer

LEXICON = {"omo": "ọmọ", "yoruba": "Yorùbá", "sango": "Ṣàngó"}


def test_restores_known_word():
    r = DictionaryRestorer(LEXICON)
    assert r.restore("omo") == "ọmọ"


def test_preserves_surrounding_punctuation_and_spacing():
    r = DictionaryRestorer(LEXICON)
    assert r.restore("Awon omo, nko?") == "Awon ọmọ, nko?"


def test_preserves_case_pattern():
    r = DictionaryRestorer(LEXICON)
    assert r.restore("Omo") == "Ọmọ"
    assert r.restore("YORUBA") == "YORÙBÁ"


def test_matches_regardless_of_input_diacritics():
    r = DictionaryRestorer(LEXICON)
    # Already-diacritized input still maps to the canonical form.
    assert r.restore("ọmọ") == "ọmọ"


def test_unknown_words_untouched():
    r = DictionaryRestorer(LEXICON)
    assert r.restore("hello world") == "hello world"


def test_satisfies_restorer_protocol():
    r = DictionaryRestorer(LEXICON)
    assert isinstance(r, Restorer)
    assert len(r) == 3


def test_rejects_bad_lexicon():
    with pytest.raises(TypeError):
        DictionaryRestorer(["not", "a", "mapping"])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        DictionaryRestorer({"k": ""})
