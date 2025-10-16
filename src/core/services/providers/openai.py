"""OpenAI provider implementation."""

from typing import Any, Dict, TYPE_CHECKING
import json
try:
    from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError, AuthenticationError as OpenAIAuthError, BadRequestError
except ModuleNotFoundError:
    OpenAI = None

from .base import BaseProvider
from .exceptions import APIError, AuthenticationError, NetworkError

if TYPE_CHECKING:
    from src.app.viewmodels.footer_viewmodel import FooterViewModel
    from src.app.viewmodels.log_viewmodel import LogViewModel

class OpenAIProvider(BaseProvider):
    """OpenAI provider."""

    def describe_image(self, encoded_image: str, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        if OpenAI is None:
            raise APIError("OpenAI Python package is not available. Install 'openai>=1.0' to enable this provider.")

        log_vm: LogViewModel = state["log_vm"]
        footer_vm: FooterViewModel = state["footer_vm"]

        api_key = state.get("openai_api_key") or ""
        model_id = state.get("llm_model") or ""
        vision_detail = str(state.get("vision_detail", "auto")).lower()

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

            log_vm.add_log(f"[API RAW OUTPUT]\n{response_text}", "info")

            total_tokens = response.usage.total_tokens
            if total_tokens is not None:
                log_vm.add_log(f"[TOKEN USAGE] +{total_tokens} tokens", "token")
                footer_vm.total_tokens = footer_vm.total_tokens + int(total_tokens)

            return json.loads(response_text)

        except OpenAIAuthError as e:
            raise AuthenticationError("Invalid OpenAI API key. Please check your settings.") from e
        except RateLimitError as e:
            raise APIError("OpenAI rate limit exceeded. Please wait and try again.") from e
        except BadRequestError as e:
            raise APIError(f"OpenAI received a bad request. This may be due to an issue with the prompt or image. Details: {e.message}") from e
        except APIStatusError as e:
            raise APIError(f"OpenAI API error ({e.status_code}): {e.message}") from e
        except APIConnectionError as e:
            raise NetworkError(f"Could not connect to OpenAI API: {e}") from e
        except json.JSONDecodeError as e:
            raise APIError(f"Model response was not valid JSON: {e}") from e
        except Exception as e:
            raise APIError(f"An unexpected error occurred with OpenAI: {e}") from e
