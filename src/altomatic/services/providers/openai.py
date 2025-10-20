"""OpenAI provider implementation."""

from typing import Any, Dict
import json

try:
    from openai import (
        OpenAI,
        RateLimitError,
        APIStatusError,
        APIConnectionError,
        AuthenticationError as OpenAIAuthError,
        BadRequestError,
    )
except ModuleNotFoundError:
    OpenAI = None

from .base import BaseProvider
from .exceptions import APIError, AuthenticationError, NetworkError
from ...ui import append_monitor_colored, update_token_label


class OpenAIProvider(BaseProvider):
    """OpenAI provider."""

    def describe_image(self, encoded_image: str, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        if OpenAI is None:
            raise APIError("OpenAI Python package is not available. Install 'openai>=1.0' to enable this provider.")

        api_key = state["openai_api_key"].get()
        model_id = state["llm_model"].get()
        vision_detail = state["vision_detail"].get().lower()

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

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(**payload)

            response_text = response.choices[0].message.content
            if not response_text:
                raise APIError("Model returned no textual output.")

            append_monitor_colored(state, f"[API RAW OUTPUT]\n{response_text}", "info")

            total_tokens = response.usage.total_tokens
            if total_tokens is not None:
                append_monitor_colored(state, f"[TOKEN USAGE] +{total_tokens} tokens", "token")
                previous = state["total_tokens"].get()
                state["total_tokens"].set(previous + total_tokens)
                update_token_label(state)

            return json.loads(response_text)

        except OpenAIAuthError as e:
            raise AuthenticationError("Invalid OpenAI API key. Please check your settings.") from e
        except RateLimitError as e:
            raise APIError("OpenAI rate limit exceeded. Please wait and try again.") from e
        except BadRequestError as e:
            raise APIError(
                f"OpenAI received a bad request. This may be due to an issue with the prompt or image. "
                f"Details: {e.message}"
            ) from e
        except APIStatusError as e:
            raise APIError(f"OpenAI API error ({e.status_code}): {e.message}") from e
        except APIConnectionError as e:
            raise NetworkError(f"Could not connect to OpenAI API: {e}") from e
        except json.JSONDecodeError as e:
            raise APIError(f"Model response was not valid JSON: {e}") from e
        except Exception as e:
            raise APIError(f"An unexpected error occurred with OpenAI: {e}") from e
