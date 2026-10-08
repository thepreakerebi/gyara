"""Tests for the pure parts of runtime (token resolution, dotenv, encoder adapter)."""

import pytest

from gyara.normalize import TokenBudget
from gyara.runtime import encoder_from_tokenizer, load_dotenv, resolve_token


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))


def test_resolve_token_prefers_argument():
    assert resolve_token("abc") == "abc"


def test_resolve_token_reads_env(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "from-env")
    assert resolve_token() == "from-env"


def test_resolve_token_raises_when_absent(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        resolve_token()


def test_encoder_adapts_tokenizer_for_token_budget():
    encode = encoder_from_tokenizer(FakeTokenizer())
    budget = TokenBudget(encode, limit=10)
    assert budget.count("a b c") == 3
    assert budget.fits("a b c")


def test_encoder_rejects_object_without_encode():
    with pytest.raises(TypeError):
        encoder_from_tokenizer(object())


def test_load_dotenv_sets_missing_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("HF_TOKEN='secret'\n# comment\nEMPTY\nOTHER=value\n")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("OTHER", raising=False)
    load_dotenv(env)
    import os

    assert os.environ["HF_TOKEN"] == "secret"
    assert os.environ["OTHER"] == "value"


def test_load_dotenv_does_not_overwrite(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("HF_TOKEN=new\n")
    monkeypatch.setenv("HF_TOKEN", "existing")
    load_dotenv(env)
    import os

    assert os.environ["HF_TOKEN"] == "existing"


def test_load_dotenv_ignores_missing_file(tmp_path):
    load_dotenv(tmp_path / "nope.env")  # no raise
