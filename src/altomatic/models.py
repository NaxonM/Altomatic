"""Model metadata and pricing information."""

from __future__ import annotations

AVAILABLE_MODELS: dict[str, dict[str, float | str]] = {
    "gpt-4.1-nano": {
        "label": "GPT-4.1 nano",
        "input_price": 0.10,
        "output_price": 0.40,
    },
    "gpt-4.1-mini": {
        "label": "GPT-4.1 mini",
        "input_price": 0.40,
        "output_price": 1.60,
    },
    "gpt-5-nano": {
        "label": "GPT-5 nano",
        "input_price": 0.05,
        "output_price": 0.40,
    },
    "gpt-5-mini": {
        "label": "GPT-5 mini",
        "input_price": 0.25,
        "output_price": 2.00,
    },
}

DEFAULT_MODEL = "gpt-5-nano"


def format_pricing(model_id: str) -> str:
    details = AVAILABLE_MODELS.get(model_id)
    if not details:
        return "Pricing unavailable"
    return (
        f"Input: ${details['input_price']:.2f} / 1M tokens | "
        f"Output: ${details['output_price']:.2f} / 1M tokens"
    )
