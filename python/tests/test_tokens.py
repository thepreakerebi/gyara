import pytest

from gyara.normalize import NATLAS_CONTEXT_LIMIT, TokenBudget


def word_encoder(text: str) -> list[int]:
    """Fake tokenizer: one token per whitespace word. Deterministic, GPU-free."""
    return list(range(len(text.split())))


def char_encoder(text: str) -> list[int]:
    """Fake tokenizer: one token per non-space character (dense, like diacritics)."""
    return [ord(c) for c in text if not c.isspace()]


def test_default_limit_is_natlas_context():
    assert TokenBudget(word_encoder).limit == NATLAS_CONTEXT_LIMIT == 8092


def test_count_and_fits():
    budget = TokenBudget(word_encoder, limit=5)
    assert budget.count("a b c") == 3
    assert budget.fits("a b c")
    assert budget.fits("a b c", reserved=2)
    assert not budget.fits("a b c d", reserved=2)


def test_report_ratios():
    budget = TokenBudget(char_encoder, limit=100)
    report = budget.report("omo")  # 3 chars, 1 word, 3 tokens
    assert report.words == 1
    assert report.tokens == 3
    assert report.tokens_per_word == 3.0
    assert report.tokens_per_char == 1.0


def test_report_handles_empty_text():
    report = TokenBudget(char_encoder).report("")
    assert report.tokens == 0
    assert report.tokens_per_word == 0.0
    assert report.tokens_per_char == 0.0


def test_truncate_drops_trailing_words_to_fit():
    budget = TokenBudget(word_encoder, limit=3)
    assert budget.truncate("a b c d e f") == "a b c"
    # Already fits -> unchanged.
    assert budget.truncate("a b") == "a b"


def test_chunk_splits_and_overlaps():
    budget = TokenBudget(word_encoder, limit=2)
    assert budget.chunk("a b c d e") == ["a b", "c d", "e"]
    # overlap repeats the last word of each chunk; full coverage, no trailing singleton.
    assert budget.chunk("a b c d", overlap_words=1) == ["a b", "b c", "c d"]


def test_chunk_makes_progress_when_single_word_exceeds_budget():
    budget = TokenBudget(char_encoder, limit=2)  # "ccc" is 3 tokens > 2
    assert budget.chunk("a ccc b") == ["a", "ccc", "b"]


def test_empty_chunk_is_empty_list():
    assert TokenBudget(word_encoder).chunk("   ") == []


def test_constructor_validation():
    with pytest.raises(TypeError):
        TokenBudget("not callable")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        TokenBudget(word_encoder, limit=0)
