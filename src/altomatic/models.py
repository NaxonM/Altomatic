"""Model metadata and pricing information."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from threading import Lock, RLock
from typing import Any, Callable

from .services.openrouter_catalog import load_catalog, refresh_catalog


@dataclass
class AppState:
    """A typed dataclass to hold the application's state."""

    root: tk.Tk
    menubar: tk.Menu
    input_type: tk.StringVar
    input_path: tk.StringVar
    recursive_search: tk.BooleanVar
    show_results_table: tk.BooleanVar
    custom_output_path: tk.StringVar
    output_folder_option: tk.StringVar
    openai_api_key: tk.StringVar
    openrouter_api_key: tk.StringVar
    proxy_enabled: tk.BooleanVar
    proxy_override: tk.StringVar
    filename_language: tk.StringVar
    alttext_language: tk.StringVar
    name_detail_level: tk.StringVar
    vision_detail: tk.StringVar
    ocr_enabled: tk.BooleanVar
    tesseract_path: tk.StringVar
    ocr_language: tk.StringVar
    ui_theme: tk.StringVar
    openai_model: tk.StringVar
    openrouter_model: tk.StringVar
    llm_provider: tk.StringVar
    llm_model: tk.StringVar
    prompt_key: tk.StringVar
    context_text: tk.StringVar
    status_var: tk.StringVar
    image_count: tk.StringVar
    total_tokens: tk.IntVar
    token_lock: Lock
    logs: list[tuple[str, str]]
    prompts: dict[str, Any]
    prompt_names: list[str]
    temp_drop_folder: str | None
    provider_model_map: dict[str, str]
    _proxy_last_settings: tuple[bool, str] | None

    _trace_callbacks: dict = field(default_factory=dict)

    # UI Widgets (optional to avoid circular dependencies if moved)
    input_card: tk.Widget | None = None
    input_entry: tk.Widget | None = None
    notebook: ttk.Notebook | None = None
    status_label: tk.Widget | None = None
    progress_bar: ttk.Progressbar | None = None
    process_button: tk.Widget | None = None
    lbl_token_usage: tk.Widget | None = None
    summary_label: tk.Widget | None = None
    custom_output_label: tk.Widget | None = None
    custom_output_entry: tk.Widget | None = None
    custom_output_browse_button: tk.Widget | None = None
    proxy_detected_label: tk.StringVar | None = None
    proxy_effective_label: tk.StringVar | None = None

    def __post_init__(self):
        """Initialize fields that depend on other fields."""
        if self.proxy_detected_label is None:
            self.proxy_detected_label = tk.StringVar(value="N/A")
        if self.proxy_effective_label is None:
            self.proxy_effective_label = tk.StringVar(value="N/A")

_MODELS_LOCK = RLock()
DEFAULT_PROVIDER = "openai"
DEFAULT_OPENROUTER_FALLBACK = "mistralai/mistral-small-3.2-24b-instruct:free"

PROVIDER_LABELS: dict[str, str] = {
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
}

_OPENAI_MODELS: dict[str, dict[str, float | str]] = {
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

_FALLBACK_OPENROUTER_MODELS: dict[str, dict[str, float | str]] = {
    "qwen/qwen2.5-vl-32b-instruct:free": {
        "label": "Qwen2.5 VL 32B (free)",
        "input_price": 0.0,
        "output_price": 0.0,
    },
    "mistralai/mistral-small-3.2-24b-instruct:free": {
        "label": "Mistral Small 3.2 24B (free)",
        "input_price": 0.0,
        "output_price": 0.0,
    },
    "google/gemma-3-12b-it:free": {
        "label": "Gemma 3 12B (free)",
        "input_price": 0.0,
        "output_price": 0.0,
    },
}

_OPENROUTER_MODELS_CACHE: dict[str, dict[str, float | str]] | None = None


def _build_openrouter_models(force_refresh: bool = False) -> dict[str, dict[str, float | str]]:
    with _MODELS_LOCK:
        global _OPENROUTER_MODELS_CACHE
        if _OPENROUTER_MODELS_CACHE is not None and not force_refresh:
            return _OPENROUTER_MODELS_CACHE

        catalog: dict[str, Any]
        try:
            catalog = load_catalog(force_refresh=force_refresh)
        except (IOError, ValueError):
            catalog = {}

        if not catalog:
            models = {model_id: dict(details) for model_id, details in _FALLBACK_OPENROUTER_MODELS.items()}
        else:
            models = {}
            for model_id, entry in catalog.items():
                models[model_id] = {
                    "label": entry.get("label", model_id),
                    "input_price": float(entry.get("input_price", 0.0) or 0.0),
                    "output_price": float(entry.get("output_price", 0.0) or 0.0),
                    "vendor": entry.get("vendor"),
                }

        _OPENROUTER_MODELS_CACHE = models
        return models


def refresh_openrouter_models() -> dict[str, dict[str, float | str]]:
    """Force-refresh the OpenRouter catalog and update the in-memory cache."""
    with _MODELS_LOCK:
        global _OPENROUTER_MODELS_CACHE
        try:
            refreshed = refresh_catalog()
        except Exception:
            return _build_openrouter_models(force_refresh=False)

        _OPENROUTER_MODELS_CACHE = {
            model_id: {
                "label": entry.get("label", model_id),
                "input_price": float(entry.get("input_price", 0.0) or 0.0),
                "output_price": float(entry.get("output_price", 0.0) or 0.0),
                "vendor": entry.get("vendor"),
            }
            for model_id, entry in refreshed.items()
        }
        PROVIDER_MODELS["openrouter"] = _OPENROUTER_MODELS_CACHE
        return _OPENROUTER_MODELS_CACHE


def _select_default_model(provider: str) -> str:
    models = get_models_for_provider(provider)
    if models:
        return next(iter(models.keys()))
    if provider == "openrouter":
        return DEFAULT_OPENROUTER_FALLBACK
    return "gpt-5-nano"


def get_models_for_provider(provider: str) -> dict[str, dict[str, float | str]]:
    if provider == "openai":
        return _OPENAI_MODELS
    if provider == "openrouter":
        return _build_openrouter_models()
    return {}


def get_provider_label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, provider.title())


def get_default_model(provider: str) -> str:
    return default_models().get(provider, DEFAULT_MODEL)


def get_provider_hint(provider: str, model_id: str) -> str | None:
    details = get_models_for_provider(provider).get(model_id)
    if not details:
        return None
    if provider == "openrouter":
        return None
    return details.get("provider_hint")  # type: ignore[return-value]


def format_pricing(provider: str, model_id: str) -> str:
    details = get_models_for_provider(provider).get(model_id)
    if not details:
        return "Pricing unavailable"

    input_price = details.get("input_price")
    output_price = details.get("output_price")

    try:
        prompt_cost = float(input_price) if input_price is not None else None
        completion_cost = float(output_price) if output_price is not None else None
    except (TypeError, ValueError):
        prompt_cost = completion_cost = None

    if prompt_cost == 0 and completion_cost == 0:
        return "Free tier (usage limits apply)"

    if prompt_cost is None or completion_cost is None:
        return "Pricing unavailable"

    return f"Input: ${prompt_cost:.2f} / 1M tokens | " f"Output: ${completion_cost:.2f} / 1M tokens"


# --- Module-level constants initialized below ---

PROVIDER_MODELS: dict[str, dict[str, dict[str, float | str]]] = {
    "openai": _OPENAI_MODELS,
    "openrouter": _build_openrouter_models(),
}

def default_models() -> dict[str, str]:
    return {
        "openai": "gpt-5-nano",
        "openrouter": _select_default_model("openrouter"),
    }

DEFAULT_MODEL = default_models()[DEFAULT_PROVIDER]
AVAILABLE_MODELS: dict[str, dict[str, float | str]] = PROVIDER_MODELS[DEFAULT_PROVIDER]
AVAILABLE_PROVIDERS = tuple(PROVIDER_MODELS.keys())
