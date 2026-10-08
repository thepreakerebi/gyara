"""Diacritic restoration for Nigerian languages.

Yoruba and Hausa carry meaning in tone marks and sub-dots (``ọwọ́`` vs ``owo``),
but people usually type them undiacritized, which degrades N-ATLAS output.

Full restoration is contextual and ultimately a model's job. This module ships a
deterministic, dependency-free **baseline**: a dictionary restorer that maps an
undiacritized word to its most frequent diacritized form from a supplied lexicon.
The :class:`Restorer` protocol lets a learned restorer drop in later without
changing call sites.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from .text import strip_diacritics

__all__ = ["Restorer", "DictionaryRestorer"]

# Word = run of letters/marks; everything else (spaces, punctuation) is preserved.
_WORD_RE = re.compile(r"\w+", re.UNICODE)


@runtime_checkable
class Restorer(Protocol):
    """Anything that restores diacritics in a string."""

    def restore(self, text: str) -> str: ...


def _match_case(source: str, target: str) -> str:
    """Apply ``source``'s casing pattern to ``target``."""
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


class DictionaryRestorer:
    """Baseline restorer backed by a lexicon of canonical diacritized forms.

    The lexicon maps canonical (diacritized) words to themselves, or undiacritized
    keys to their diacritized form. Lookups are accent- and case-insensitive; the
    original word's capitalisation is preserved in the output.

    Args:
        lexicon: Mapping whose values are the canonical diacritized words.

    Example:
        >>> r = DictionaryRestorer({"ọmọ": "ọmọ", "Yorùbá": "Yorùbá"})
        >>> r.restore("Awon omo")
        'Awon ọmọ'
    """

    def __init__(self, lexicon: Mapping[str, str]) -> None:
        if not isinstance(lexicon, Mapping):
            raise TypeError("lexicon must be a mapping")
        self._map: dict[str, str] = {}
        for value in lexicon.values():
            if not isinstance(value, str) or not value:
                raise ValueError("lexicon values must be non-empty strings")
            key = strip_diacritics(value).lower()
            # First writer wins, so pass the most frequent form first if it matters.
            self._map.setdefault(key, value)

    def __len__(self) -> int:
        return len(self._map)

    def restore(self, text: str) -> str:
        """Return ``text`` with known undiacritized words replaced by canonical forms."""
        if not isinstance(text, str):
            raise TypeError("text must be a str")

        def replace(match: re.Match[str]) -> str:
            word = match.group(0)
            canonical = self._map.get(strip_diacritics(word).lower())
            return _match_case(word, canonical) if canonical else word

        return _WORD_RE.sub(replace, text)
