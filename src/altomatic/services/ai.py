"""LLM integration layer."""

from __future__ import annotations

import json
from typing import Any

import requests
from openai import OpenAI

from ..models import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    get_default_model,
    get_models_for_provider,
    get_provider_hint,
    get_provider_label,
)
from ..prompts import get_prompt_template
from ..ui import append_monitor_colored, update_token_label
from ..utils import extract_text_from_image, image_to_base64


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/MehdiDevX/Altomatic",
    "X-Title": "Altomatic",
    "Accept": "application/json",
}


def _extract_response_text(payload) -> str | None:
    if payload is None:
        return None

    if isinstance(payload, str):
        return payload.strip() or None

    if isinstance(payload, dict):
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"].strip() or None

        output_field = payload.get("output_text")
        if isinstance(output_field, list):
            collected = [segment.strip() for segment in output_field if isinstance(segment, str) and segment.strip()]
            if collected:
                return "\n".join(collected)

        if "output" in payload and isinstance(payload["output"], list):
            parts: list[str] = []
            for item in payload["output"]:
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, list):
                        for segment in content:
                            if isinstance(segment, dict):
                                text = segment.get("text")
                                if text:
                                    parts.append(str(text).strip())
                            elif isinstance(segment, str) and segment.strip():
                                parts.append(segment.strip())
                    elif isinstance(content, str) and content.strip():
                        parts.append(content.strip())
                    elif isinstance(item.get("text"), str) and item["text"].strip():
                        parts.append(item["text"].strip())
                elif isinstance(item, str) and item.strip():
                    parts.append(item.strip())
            if parts:
                return "\n".join(parts)

        if "choices" in payload and isinstance(payload["choices"], list):
            parts: list[str] = []
            for choice in payload["choices"]:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, list):
                        for segment in content:
                            if isinstance(segment, dict):
                                text = segment.get("text")
                                if text:
                                    parts.append(str(text).strip())
                            elif isinstance(segment, str) and segment.strip():
                                parts.append(segment.strip())
                    elif isinstance(content, str) and content.strip():
                        parts.append(content.strip())
                text_field = choice.get("text")
                if isinstance(text_field, str) and text_field.strip():
                    parts.append(text_field.strip())
            if parts:
                return "\n".join(parts)

        if "content" in payload and isinstance(payload["content"], list):
            parts = []
            for segment in payload["content"]:
                if isinstance(segment, dict):
                    text = segment.get("text")
                    if text:
                        parts.append(str(text).strip())
                elif isinstance(segment, str) and segment.strip():
                    parts.append(segment.strip())
            if parts:
                return "\n".join(parts)

        if "response" in payload:
            nested = _extract_response_text(payload["response"])
            if nested:
                return nested

    if isinstance(payload, list):
        parts = []
        for item in payload:
            text = _extract_response_text(item)
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts)

    return None


def _call_openrouter(api_key: str, payload: dict[str, Any], provider_hint: str | None) -> dict[str, Any]:
    request_payload = dict(payload)
    if provider_hint:
        request_payload = dict(request_payload)
        request_payload["provider"] = {"order": [provider_hint], "allow_fallbacks": False}

    headers = {
        **OPENROUTER_HEADERS,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        json=request_payload,
        headers=headers,
        timeout=90,
    )

    try:
        data = response.json()
    except ValueError:
        snippet = response.text[:1200]
        raise ValueError(f"Unexpected response ({response.status_code}): {snippet}") from None

    if not response.ok:
        message = (
            data.get("error", {}).get("message")
            if isinstance(data.get("error"), dict)
            else data.get("error")
        )
        message = message or data.get("message") or response.text
        raise ValueError(f"OpenRouter error ({response.status_code}): {message}")

    return data


def describe_image(state, image_path: str) -> dict | None:
    provider_var = state.get("llm_provider")
    provider = provider_var.get() if provider_var is not None else DEFAULT_PROVIDER
    models = get_models_for_provider(provider)

    model_var = state.get("llm_model")
    model_id = model_var.get() if model_var is not None else None
    if not model_id:
        model_id = get_default_model(provider)
    if model_id not in models:
        model_id = get_default_model(provider)

    if provider == "openrouter":
        api_key = state["openrouter_api_key"].get()
    else:
        api_key = state["openai_api_key"].get()

    name_lang = state["filename_language"].get().lower()
    alt_lang = state["alttext_language"].get().lower()
    detail_level = state["name_detail_level"].get().lower()
    vision_detail = state["vision_detail"].get().lower()
    ocr_enabled = state["ocr_enabled"].get()
    tesseract_path = state["tesseract_path"].get()
    ocr_lang = state["ocr_language"].get()
    prompt_key = state["prompt_key"].get() if "prompt_key" in state else "default"
    prompt_template = get_prompt_template(prompt_key).strip()
    user_context = state["context_text"].get().strip() if "context_text" in state else ""

    provider_hint = get_provider_hint(provider, model_id) if provider == "openrouter" else None

    if ocr_enabled:
        ocr_result = extract_text_from_image(image_path, tesseract_path, ocr_lang)
        if ocr_result.startswith("⚠️ OCR failed:"):
            append_monitor_colored(state, ocr_result, "error")
            ocr_text = ""
        else:
            append_monitor_colored(state, f"[OCR RESULT] {ocr_result}", "warn")
            ocr_text = ocr_result
    else:
        ocr_text = ""

    if vision_detail not in {"low", "high"}:
        vision_detail = "high"

    encoded_image = image_to_base64(image_path)

    if not prompt_template:
        prompt_template = (
            "You are an expert image analyst. Use any provided context to guide your response.\n"
            "Return JSON with keys 'name' and 'alt'."
        )

    prompt_parts: list[str] = [prompt_template.strip()]

    if user_context:
        prompt_parts.append(f"\nContext from user:\n{user_context}")

    name_words = "1-2" if detail_level == "minimal" else ("up to 3" if detail_level == "normal" else "up to 8")
    name_display = name_lang.capitalize()
    alt_display = alt_lang.capitalize()
    prompt_parts.append(
        "\nOutput requirements:\n"
        "- 'name': lowercase, dash-separated, {} words in {} describing the key subject or purpose (no special characters or digits).\n"
        "- 'alt': single clear sentence in {} describing what is visible, mentioning key details and avoiding broad or list-like phrasing."
        .format(name_words, name_display, alt_display)
    )

    if ocr_text:
        prompt_parts.append(f"\nText detected via OCR:\n{ocr_text}")

    prompt_parts.append(
        "\nRespond ONLY with a valid JSON object containing 'name' and 'alt'."
    )

    prompt = "\n".join(prompt_parts)

    provider_label = get_provider_label(provider)
    append_monitor_colored(state, f"[LLM] Provider={provider_label} | Model={model_id}", "debug")

    try:
        response_payload: dict[str, Any] | None = None
        response_text: str | None = None
        total_tokens: int | None = None

        if provider == "openrouter":
            payload: dict[str, Any] = {
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

            response_payload = _call_openrouter(api_key, payload, provider_hint)
            response_text = _extract_response_text(response_payload)
            usage_data = response_payload.get("usage") if isinstance(response_payload, dict) else None
            if isinstance(usage_data, dict):
                token_value = usage_data.get("total_tokens") or usage_data.get("total")
                if token_value is not None:
                    total_tokens = int(token_value)
        else:
            payload = {
                "model": model_id,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": encoded_image, "detail": vision_detail},
                        ],
                    }
                ],
                "text": {"format": {"type": "json_object"}},
            }

            client = OpenAI(api_key=api_key)
            response_obj = client.responses.create(**payload)

            response_text = getattr(response_obj, "output_text", None)

            usage_obj = getattr(response_obj, "usage", None)
            if usage_obj is not None:
                if hasattr(usage_obj, "total_tokens") and usage_obj.total_tokens is not None:
                    total_tokens = int(usage_obj.total_tokens)
                elif isinstance(usage_obj, dict):
                    token_value = usage_obj.get("total_tokens") or usage_obj.get("total")
                    if token_value is not None:
                        total_tokens = int(token_value)

            if hasattr(response_obj, "model_dump"):
                try:
                    response_payload = response_obj.model_dump()
                except Exception:
                    response_payload = None
            elif hasattr(response_obj, "to_dict"):
                try:
                    response_payload = response_obj.to_dict()
                except Exception:
                    response_payload = None
            elif isinstance(response_obj, dict):
                response_payload = response_obj
            elif isinstance(response_obj, str):
                try:
                    response_payload = json.loads(response_obj)
                except json.JSONDecodeError:
                    response_payload = None
            elif hasattr(response_obj, "model_dump_json"):
                try:
                    response_payload = json.loads(response_obj.model_dump_json())
                except Exception:
                    response_payload = None

        if response_payload is None and response_text:
            response_payload = {"output_text": response_text}

        if response_text is None and response_payload is not None:
            response_text = _extract_response_text(response_payload)

        if not response_text:
            raise ValueError("Model returned no textual output")

        append_monitor_colored(state, f"[API RAW OUTPUT]\n{response_text}", "info")

        if total_tokens is None and isinstance(response_payload, dict):
            usage_data = response_payload.get("usage")
            if isinstance(usage_data, dict):
                token_value = usage_data.get("total_tokens") or usage_data.get("total")
                if token_value is not None:
                    total_tokens = int(token_value)

        if total_tokens is not None:
            append_monitor_colored(state, f"[TOKEN USAGE] +{total_tokens} tokens", "token")
            previous = state["total_tokens"].get()
            state["total_tokens"].set(previous + total_tokens)
            update_token_label(state)

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as json_error:
            raise ValueError(f"Model response was not valid JSON: {json_error}") from json_error

    except Exception as exc:
        append_monitor_colored(state, f"[API ERROR:{provider_label}] {exc}", "error")
        return None
