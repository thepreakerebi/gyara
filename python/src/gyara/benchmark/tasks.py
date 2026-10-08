"""Extraction tasks for the structured-output benchmark.

Each task is a (name, prompt, schema) triple in a Nigerian context. The point is to
make the base model emit valid JSON for a schema; raw prompting often fails, while
Gyara's constrained decoding is valid by construction. The set is deliberately small
and extensible — add rows to grow the benchmark.
"""

from __future__ import annotations

__all__ = ["TASKS"]

_TRANSFER = {
    "type": "object",
    "properties": {"recipient": {"type": "string"}, "amount_naira": {"type": "integer"}},
    "required": ["recipient", "amount_naira"],
    "additionalProperties": False,
}

_CONTACT = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "phone": {"type": "string"}},
    "required": ["name", "phone"],
    "additionalProperties": False,
}

_ORDER = {
    "type": "object",
    "properties": {
        "item": {"type": "string"},
        "quantity": {"type": "integer"},
        "market": {"type": "string"},
    },
    "required": ["item", "quantity"],
    "additionalProperties": False,
}

_SENTIMENT = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": ["positive", "negative", "neutral"]}},
    "required": ["label"],
    "additionalProperties": False,
}

TASKS: list[tuple[str, str, dict]] = [
    ("transfer_en", "Extract recipient and amount: 'Send 5k to Chidi for market'.", _TRANSFER),
    ("transfer_pidgin", "Extract recipient and amount: 'Abeg send 2k give Ada quick'.", _TRANSFER),
    ("contact", "Extract name and phone: 'Call Bisi on 08031234567 tomorrow'.", _CONTACT),
    ("order_yoruba", "Extract item and quantity: 'Mo fe ra garri meji ni oja Mushin'.", _ORDER),
    ("order_en", "Extract item, quantity and market: 'Buy 3 bags of rice at Oyingbo'.", _ORDER),
    ("sentiment_pos", "Classify sentiment: 'This jollof sweet die, I enjoy am!'.", _SENTIMENT),
    ("sentiment_neg", "Classify sentiment: 'The network bad today, I vex.'.", _SENTIMENT),
    ("sentiment_neutral", "Classify sentiment: 'The meeting is by 2pm.'.", _SENTIMENT),
]
