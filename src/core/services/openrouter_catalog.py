"""Fetch and cache OpenRouter model metadata."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests

from ..utils import configure_global_proxy, get_requests_proxies

CATALOG_URL = "https://openrouter.ai/api/v1/models"
CATALOG_FILENAME = "openrouter_models.json"
CACHE_TTL_SECONDS = 24 * 60 * 60  # refresh once per day by default


@dataclass
class OpenRouterModel:
    """Structured information about a single OpenRouter model."""

    model_id: str
    label: str
    vendor: str | None
    input_price: float
    output_price: float

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "OpenRouterModel | None":
        architecture = payload.get("architecture") or {}
        modalities: Iterable[str] = architecture.get("input_modalities") or []
        normalized_modalities = {str(item).lower() for item in modalities}
        if "image" not in normalized_modalities:
            return None

        pricing = payload.get("pricing") or {}

        def _parse_price(key: str) -> float:
            value = pricing.get(key)
            if value in (None, ""):
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        if any(_parse_price(field) > 0 for field in ("prompt", "completion", "image", "request")):
            return None

        model_id = payload.get("id")
        if not model_id:
            return None

        label = payload.get("name") or model_id
        if "free" not in label.lower():
            label = f"{label.strip()} (free)"
        vendor = None
        if isinstance(model_id, str) and "/" in model_id:
            vendor = model_id.split("/", 1)[0]

        return cls(
            model_id=model_id,
            label=label,
            vendor=vendor,
            input_price=_parse_price("prompt"),
            output_price=_parse_price("completion"),
        )


def _catalog_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / CATALOG_FILENAME


def _load_catalog_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _save_catalog_file(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _is_stale(catalog: dict[str, Any]) -> bool:
    fetched_at = catalog.get("fetched_at")
    if not isinstance(fetched_at, (int, float)):
        return True
    return (time.time() - fetched_at) > CACHE_TTL_SECONDS


def _serialize(models: list[OpenRouterModel]) -> dict[str, Any]:
    return {
        "fetched_at": time.time(),
        "models": [
            {
                "id": model.model_id,
                "label": model.label,
                "vendor": model.vendor,
                "input_price": model.input_price,
                "output_price": model.output_price,
            }
            for model in models
        ],
    }


def _deserialize(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    models = {}
    for entry in payload.get("models", []):
        model_id = entry.get("id")
        if not model_id:
            continue
        label = entry.get("label", model_id)
        if "free" not in str(label).lower():
            label = f"{label.strip()} (free)"
        models[model_id] = {
            "label": label,
            "vendor": entry.get("vendor"),
            "input_price": float(entry.get("input_price", 0.0) or 0.0),
            "output_price": float(entry.get("output_price", 0.0) or 0.0),
        }
    return models


def fetch_openrouter_models() -> list[OpenRouterModel]:
    configure_global_proxy()
    proxies = get_requests_proxies()

    response = requests.get(
        CATALOG_URL,
        timeout=45,
        proxies=proxies or None,
    )
    response.raise_for_status()
    payload = response.json()
    models: list[OpenRouterModel] = []
    for entry in payload.get("data", []):
        model = OpenRouterModel.from_api(entry)
        if model is None:
            continue
        models.append(model)
    return models


def refresh_catalog() -> dict[str, dict[str, Any]]:
    models = fetch_openrouter_models()
    serialized = _serialize(models)
    _save_catalog_file(_catalog_path(), serialized)
    return _deserialize(serialized)


def load_catalog(force_refresh: bool = False) -> dict[str, dict[str, Any]]:
    path = _catalog_path()
    catalog = _load_catalog_file(path)
    if force_refresh or catalog is None or _is_stale(catalog):
        try:
            return refresh_catalog()
        except Exception:
            if catalog is None:
                raise
    if catalog is None:
        return {}
    return _deserialize(catalog)
