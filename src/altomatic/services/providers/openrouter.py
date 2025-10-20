"""OpenRouter provider implementation."""

import json
from typing import Any, Dict

import requests

from .base import BaseProvider
from .exceptions import APIError, AuthenticationError, NetworkError
from ...ui import append_monitor_colored, update_token_label
from ...models import get_provider_hint
from ...utils.text import extract_json_from_string

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/MehdiDevX/Altomatic",
    "X-Title": "Altomatic",
    "Accept": "application/json",
}


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider."""

    def describe_image(self, encoded_image: str, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        api_key = state["openrouter_api_key"].get()
        model_id = state["llm_model"].get()
        vision_detail = state["vision_detail"].get().lower()
        proxies = state.get("proxies")
        provider_hint = get_provider_hint("openrouter", model_id)

        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": encoded_image, "detail": vision_detail},
                        },
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }

        if provider_hint:
            payload["provider"] = {"order": [provider_hint], "allow_fallbacks": False}

        headers = {
            **OPENROUTER_HEADERS,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=90,
                proxies=proxies or None,
            )
            response.raise_for_status()

            data = response.json()
            response_text = self._extract_response_text(data)

            if not response_text:
                raise APIError("Model returned no textual output.")

            append_monitor_colored(state, f"[API RAW OUTPUT]\n{response_text}", "info")

            json_result = extract_json_from_string(response_text)
            if not json_result:
                raise APIError("Model response was not valid JSON.")

            usage_data = data.get("usage")
            if isinstance(usage_data, dict):
                total_tokens = usage_data.get("total_tokens") or usage_data.get("total")
                if total_tokens is not None:
                    append_monitor_colored(state, f"[TOKEN USAGE] +{total_tokens} tokens", "token")
                    previous = state["total_tokens"].get()
                    state["total_tokens"].set(previous + int(total_tokens))
                    update_token_label(state)

            return json_result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid OpenRouter API key.") from e

            try:
                error_data = e.response.json()
                error_details = error_data.get("error", {})

                # Prioritize the most specific error message from the underlying provider
                provider_message = error_details.get("provider_error", {}).get("message")
                if provider_message:
                    message = f"Provider returned error: {provider_message}"
                else:
                    # Fallback to the main error message from OpenRouter
                    message = error_details.get("message", e.response.text)
            except json.JSONDecodeError:
                # If the response is not JSON, use the raw text
                message = e.response.text

            raise APIError(f"OpenRouter API error ({e.response.status_code}): {message}") from e

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Could not connect to OpenRouter API: {e}") from e
        except Exception as e:
            raise APIError(f"An unexpected error occurred with OpenRouter: {e}") from e

    def _extract_response_text(self, payload: Any) -> str | None:
        if payload is None:
            return None

        if isinstance(payload, str):
            return payload.strip() or None

        if isinstance(payload, dict):
            choices = payload.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content.strip() or None

        return self._deep_extract(payload)

    def _deep_extract(self, payload: Any) -> str | None:
        if isinstance(payload, str):
            return payload.strip() or None

        if isinstance(payload, dict):
            if isinstance(payload.get("output_text"), str):
                return payload["output_text"].strip() or None

            for key in ["content", "text", "output", "response"]:
                if key in payload:
                    result = self._deep_extract(payload[key])
                    if result:
                        return result

            if "choices" in payload:
                result = self._deep_extract(payload["choices"])
                if result:
                    return result

        if isinstance(payload, list) and payload:
            for item in payload:
                result = self._deep_extract(item)
                if result:
                    return result

        return None
