"""LLM integration layer."""

from __future__ import annotations

import os

from ..models import DEFAULT_PROVIDER
from ..prompts import get_prompt_template
from ..services.providers.openai import OpenAIProvider
from ..services.providers.openrouter import OpenRouterProvider
from ..utils import (
    configure_global_proxy,
    extract_text_from_image,
    get_requests_proxies,
    image_to_base64,
    preprocess_image_for_llm,
)
from ..ui import append_monitor_colored


def get_provider(provider_name: str):
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def describe_image(state, image_path: str) -> dict | None:
    proxy_enabled = state.get("proxy_enabled").get() if "proxy_enabled" in state else True
    proxy_override = state.get("proxy_override").get().strip() if "proxy_override" in state else ""
    configure_global_proxy(enabled=proxy_enabled, override=proxy_override or None, force=False)
    proxies = get_requests_proxies(enabled=proxy_enabled, override=proxy_override or None)
    state["proxies"] = proxies

    provider_name = state.get("llm_provider").get() or DEFAULT_PROVIDER

    provider = get_provider(provider_name)

    name_lang = state["filename_language"].get().lower()
    alt_lang = state["alttext_language"].get().lower()
    detail_level = state["name_detail_level"].get().lower()
    ocr_enabled = state["ocr_enabled"].get()
    tesseract_path = state["tesseract_path"].get()
    ocr_lang = state["ocr_language"].get()
    prompt_key = state["prompt_key"].get() if "prompt_key" in state else "default"
    prompt_template = get_prompt_template(prompt_key).strip()
    user_context = state["context_text"].get().strip() if "context_text" in state else ""

    ocr_text = ""
    if ocr_enabled:
        ocr_result = extract_text_from_image(image_path, tesseract_path, ocr_lang)
        if ocr_result.startswith("⚠️ OCR failed:"):
            append_monitor_colored(state, ocr_result, "error")
        else:
            append_monitor_colored(state, f"[OCR RESULT] {ocr_result}", "warn")
            ocr_text = ocr_result

    try:
        processed_image = preprocess_image_for_llm(image_path)
        encoded_image = processed_image.data_url

        def _bytes_to_kb(value: int) -> float:
            return value / 1024 if value else 0.0

        original_kb = _bytes_to_kb(processed_image.original_size_bytes)
        processed_kb = _bytes_to_kb(processed_image.processed_size_bytes)
        delta = original_kb - processed_kb
        pct = (delta / original_kb * 100) if original_kb else 0
        resized_note = " • resized" if processed_image.resized else ""
        quality_note = (
            f" • quality={processed_image.quality}" if processed_image.quality is not None else ""
        )
        append_monitor_colored(
            state,
            (
                f"[IMAGE PREPROCESS] {os.path.basename(image_path)}: "
                f"{original_kb:.0f} KB → {processed_kb:.0f} KB ({pct:.0f}% smaller)"
                f" • format={processed_image.format}{quality_note}{resized_note}"
            ),
            "info",
        )
    except Exception as e:
        append_monitor_colored(state, f"[IMAGE PREPROCESS] Failed to compress image: {e}", "warn")
        encoded_image = image_to_base64(image_path)
        append_monitor_colored(state, "[IMAGE PREPROCESS] Falling back to original image payload.", "warn")

    prompt_parts: list[str] = [prompt_template.strip()]
    if user_context:
        prompt_parts.append(f"\nContext from user:\n{user_context}")

    name_words = "1-2" if detail_level == "minimal" else ("up to 3" if detail_level == "normal" else "up to 8")
    prompt_parts.append(
        f"\nOutput requirements:\n- 'name': lowercase, dash-separated, {name_words} words in "
        f"{name_lang.capitalize()}.\n- 'alt': single clear sentence in {alt_lang.capitalize()}."
    )

    if ocr_text:
        prompt_parts.append(f"\nText detected via OCR:\n{ocr_text}")

    prompt_parts.append("\nRespond ONLY with a valid JSON object containing 'name' and 'alt'.")
    prompt = "\n".join(prompt_parts)

    return provider.describe_image(encoded_image, prompt, state)
