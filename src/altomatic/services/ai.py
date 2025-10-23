"""LLM integration layer."""

from __future__ import annotations

from ..models import AppState, DEFAULT_PROVIDER
from ..prompts import get_prompt_template
from ..services.providers.exceptions import OCRError
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


_provider_instances = {}


def get_provider(provider_name: str):
    if provider_name not in _provider_instances:
        if provider_name == "openai":
            _provider_instances[provider_name] = OpenAIProvider()
        elif provider_name == "openrouter":
            _provider_instances[provider_name] = OpenRouterProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    return _provider_instances[provider_name]


def describe_image(state: AppState, image_path: str) -> dict | None:
    proxy_enabled = state.proxy_enabled.get()
    proxy_override = state.proxy_override.get().strip()

    configure_global_proxy(enabled=proxy_enabled, override=proxy_override or None, force=False)
    proxies = get_requests_proxies(enabled=proxy_enabled, override=proxy_override or None)
    state.proxies = proxies

    provider_name = state.llm_provider.get() or DEFAULT_PROVIDER
    try:
        provider = get_provider(provider_name)
    except ValueError as e:
        append_monitor_colored(state, f"Error selecting provider: {e}", "error")
        return None

    name_lang = state.filename_language.get().lower()
    alt_lang = state.alttext_language.get().lower()
    detail_level = state.name_detail_level.get().lower()
    ocr_enabled = state.ocr_enabled.get()
    tesseract_path = state.tesseract_path.get()
    ocr_lang = state.ocr_language.get()
    prompt_key = state.prompt_key.get()
    prompt_template = get_prompt_template(prompt_key).strip()
    user_context = state.context_text.get().strip()

    ocr_text = ""
    if ocr_enabled:
        try:
            ocr_result = extract_text_from_image(image_path, tesseract_path, ocr_lang)
            if ocr_result:
                append_monitor_colored(state, f"[OCR RESULT] {ocr_result}", "warn")
                ocr_text = ocr_result
        except OCRError as e:
            append_monitor_colored(state, f"⚠️ OCR failed: {e}", "error")

    try:
        processed_image = preprocess_image_for_llm(image_path)
        encoded_image = processed_image.data_url
    except Exception as e:
        append_monitor_colored(state, f"[IMAGE PREPROCESS] Failed to compress image: {e}", "warn")
        encoded_image = image_to_base64(image_path)

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
