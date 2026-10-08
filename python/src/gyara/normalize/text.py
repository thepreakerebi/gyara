"""Deterministic text normalization for Nigerian-language input to N-ATLAS.

These functions are pure and dependency-free. They clean raw user text before it
reaches the model: Unicode normalization, stray zero-width characters, and
inconsistent whitespace are common sources of degraded output.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["normalize_text", "strip_diacritics", "NormalizationForm"]

NormalizationForm = str  # one of: "NFC", "NFKC", "NFD", "NFKD"
_VALID_FORMS = ("NFC", "NFKC", "NFD", "NFKD")

# Zero-width and byte-order characters that silently break tokenization/matching.
_ZERO_WIDTH = dict.fromkeys(
    map(ord, "​‌‍⁠﻿"), None
)
# Runs of horizontal whitespace (spaces, tabs, Unicode spaces) — newlines kept.
_HWS_RE = re.compile(r"[^\S\n]+")
# Three or more newlines collapse to a paragraph break.
_MULTI_NL_RE = re.compile(r"\n{3,}")


def normalize_text(
    text: str,
    *,
    form: NormalizationForm = "NFC",
    collapse_whitespace: bool = True,
    strip_zero_width: bool = True,
) -> str:
    """Return a cleaned copy of ``text``.

    Args:
        text: Raw input string.
        form: Unicode normalization form. Default ``"NFC"`` keeps diacritics as
            single composed code points, which is what the N-ATLAS tokenizer expects.
        collapse_whitespace: Collapse horizontal whitespace runs to one space and
            trim each line; limit blank runs to a single paragraph break.
        strip_zero_width: Remove zero-width and BOM characters.

    Raises:
        TypeError: If ``text`` is not a ``str``.
        ValueError: If ``form`` is not a recognised normalization form.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if form not in _VALID_FORMS:
        raise ValueError(f"form must be one of {_VALID_FORMS}, got {form!r}")

    out = unicodedata.normalize(form, text)
    if strip_zero_width:
        out = out.translate(_ZERO_WIDTH)
    if collapse_whitespace:
        out = _HWS_RE.sub(" ", out)
        out = _MULTI_NL_RE.sub("\n\n", out)
        out = "\n".join(line.strip() for line in out.split("\n")).strip()
    return out


def strip_diacritics(text: str) -> str:
    """Return ``text`` with all combining marks removed (reduced to base letters).

    Deterministic and lossy: ``"Yorùbá" -> "Yoruba"``, ``"ọmọ" -> "omo"``. Useful as
    a lookup key for diacritic restoration and for accent-insensitive matching.

    Raises:
        TypeError: If ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))
