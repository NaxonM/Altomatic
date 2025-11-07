"""Utility helpers for testing provider credentials without running a full job."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from .providers.exceptions import APIError, AuthenticationError, NetworkError
OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/MehdiDevX/Altomatic",
    "X-Title": "Altomatic",
    "Accept": "application/json",
}


def _clean_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of headers with falsy values removed."""
    return {key: value for key, value in headers.items() if value}


def check_openai_key(api_key: str, *, proxies: Optional[Dict[str, str]] = None, timeout: int = 20) -> Dict[str, Any]:
    """Perform a lightweight OpenAI credential check by listing available models."""
    if not api_key:
        raise AuthenticationError("OpenAI API key is required.")

    headers = _clean_headers(
        {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
    )

    try:
        response = requests.get(
            OPENAI_MODELS_URL,
            headers=headers,
            params={"limit": 5},
            timeout=timeout,
            proxies=proxies or None,
        )
        if response.status_code == 401:
            raise AuthenticationError("OpenAI rejected the API key.")

        response.raise_for_status()
        payload = response.json()

    except requests.exceptions.Timeout as exc:
        raise NetworkError("Timed out while contacting the OpenAI API.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise NetworkError(f"Could not reach the OpenAI API: {exc}") from exc
    except requests.exceptions.HTTPError as exc:
        message = response.text if exc.response is None else exc.response.text
        raise APIError(f"OpenAI responded with an HTTP error: {message}") from exc
    except json.JSONDecodeError as exc:
        raise APIError("OpenAI returned an unexpected response format.") from exc

    data = payload.get("data")
    if isinstance(data, list):
        model_preview = [entry.get("id") for entry in data if isinstance(entry, dict) and entry.get("id")]
    else:
        model_preview = []

    count = len(model_preview)
    message = "OpenAI reachable"
    if count:
        examples = ", ".join(model_preview[:3])
        message = f"OpenAI reachable—sample models: {examples}" if examples else "OpenAI reachable"

    return {
        "ok": True,
        "provider": "openai",
        "count": count,
        "models": model_preview,
        "message": message,
    }


def check_openrouter_key(
    api_key: str,
    *,
    proxies: Optional[Dict[str, str]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    """Perform a lightweight OpenRouter credential check by listing available models."""
    if not api_key:
        raise AuthenticationError("OpenRouter API key is required.")

    headers = _clean_headers(
        {
            **OPENROUTER_HEADERS,
            "Authorization": f"Bearer {api_key}",
        }
    )

    try:
        response = requests.get(
            f"{OPENROUTER_BASE_URL}/models",
            headers=headers,
            params={"limit": 5},
            timeout=timeout,
            proxies=proxies or None,
        )
        if response.status_code == 401:
            raise AuthenticationError("OpenRouter rejected the API key.")

        response.raise_for_status()
        payload = response.json()

    except requests.exceptions.Timeout as exc:
        raise NetworkError("Timed out while contacting the OpenRouter API.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise NetworkError(f"Could not reach the OpenRouter API: {exc}") from exc
    except requests.exceptions.HTTPError as exc:
        message = response.text if exc.response is None else exc.response.text
        raise APIError(f"OpenRouter responded with an HTTP error: {message}") from exc
    except json.JSONDecodeError as exc:
        raise APIError("OpenRouter returned an unexpected response format.") from exc

    data = payload.get("data")
    if isinstance(data, list):
        model_preview = [entry.get("id") for entry in data if isinstance(entry, dict) and entry.get("id")]
    else:
        model_preview = []

    count = len(model_preview)
    message = "OpenRouter reachable"
    if count:
        examples = ", ".join(model_preview[:3])
        message = f"OpenRouter reachable—sample models: {examples}" if examples else "OpenRouter reachable"

    quota = payload.get("limits") if isinstance(payload, dict) else None

    return {
        "ok": True,
        "provider": "openrouter",
        "count": count,
        "models": model_preview,
        "message": message,
        "quota": quota,
    }
