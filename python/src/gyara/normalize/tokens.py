"""Tokenizer-aware context budgeting for N-ATLAS.

N-ATLAS has an 8,092-token context window, and the Llama-3 tokenizer splits
Yoruba, Hausa and Igbo text into far more tokens per word than English. Text that
looks short can silently overflow the window and get truncated mid-thought.

This module measures the *true* token cost of text and fits it to a budget. It is
decode-free: it needs only an encoder (``str -> sequence of token ids``), so the
same logic runs with the real N-ATLAS tokenizer on a GPU host or with a fake
encoder in tests.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

__all__ = ["NATLAS_CONTEXT_LIMIT", "TokenReport", "TokenBudget"]

# Published N-ATLAS context length (tokens).
NATLAS_CONTEXT_LIMIT = 8092

Encoder = Callable[[str], Sequence[int]]


@dataclass(frozen=True)
class TokenReport:
    """Token-cost breakdown for a piece of text."""

    characters: int
    words: int
    tokens: int
    tokens_per_word: float
    tokens_per_char: float


class TokenBudget:
    """Measure and fit text against a token budget using an injected encoder.

    Args:
        encode: Callable mapping a string to its token ids.
        limit: Maximum tokens allowed. Defaults to N-ATLAS's context length.
    """

    def __init__(self, encode: Encoder, limit: int = NATLAS_CONTEXT_LIMIT) -> None:
        if not callable(encode):
            raise TypeError("encode must be callable")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive int")
        self._encode = encode
        self.limit = limit

    def count(self, text: str) -> int:
        """Number of tokens ``text`` encodes to."""
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        return len(self._encode(text))

    def fits(self, text: str, *, reserved: int = 0) -> bool:
        """Whether ``text`` fits within the budget, leaving ``reserved`` tokens free.

        ``reserved`` sets aside room for the model's response or a system prompt.
        """
        if reserved < 0:
            raise ValueError("reserved must be >= 0")
        return self.count(text) <= self.limit - reserved

    def report(self, text: str) -> TokenReport:
        """Return a :class:`TokenReport` for ``text`` (per-word / per-char ratios)."""
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        words = len(text.split())
        chars = len(text)
        tokens = self.count(text)
        return TokenReport(
            characters=chars,
            words=words,
            tokens=tokens,
            tokens_per_word=tokens / words if words else 0.0,
            tokens_per_char=tokens / chars if chars else 0.0,
        )

    def truncate(self, text: str, *, max_tokens: int | None = None) -> str:
        """Trim ``text`` on word boundaries so it fits within ``max_tokens``.

        Defaults to the budget limit. Decode-free: it drops whole trailing words
        until the remainder fits, so the result is always valid text.
        """
        budget = self.limit if max_tokens is None else max_tokens
        if budget <= 0:
            raise ValueError("max_tokens must be positive")
        if self.count(text) <= budget:
            return text
        words = text.split()
        # Largest prefix of words that fits (linear scan; inputs here are small).
        kept: list[str] = []
        for word in words:
            candidate = " ".join([*kept, word])
            if self.count(candidate) > budget:
                break
            kept.append(word)
        return " ".join(kept)

    def chunk(
        self, text: str, *, max_tokens: int | None = None, overlap_words: int = 0
    ) -> list[str]:
        """Split ``text`` into word-aligned chunks that each fit ``max_tokens``.

        Args:
            max_tokens: Per-chunk token budget. Defaults to the budget limit.
            overlap_words: Words repeated between consecutive chunks, for context
                continuity in retrieval.
        """
        budget = self.limit if max_tokens is None else max_tokens
        if budget <= 0:
            raise ValueError("max_tokens must be positive")
        if overlap_words < 0:
            raise ValueError("overlap_words must be >= 0")

        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = start
            kept: list[str] = []
            while end < len(words):
                candidate = " ".join([*kept, words[end]])
                if self.count(candidate) > budget:
                    break
                kept.append(words[end])
                end += 1
            if not kept:
                # A single word exceeds the budget; emit it alone to make progress.
                chunks.append(words[start])
                start += 1
                continue
            chunks.append(" ".join(kept))
            if end >= len(words):
                break
            start = max(end - overlap_words, start + 1)
        return chunks
