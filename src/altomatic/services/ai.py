"""LLM integration layer."""

from __future__ import annotations

from ..models import DEFAULT_PROVIDER
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


def describe_image(state: dict[str, Any], image_path: str) -> dict | None:
    proxy_enabled_var = state.get("proxy_enabled")
    proxy_enabled = proxy_enabled_var.get() if proxy_enabled_var else True
    proxy_override_var = state.get("proxy_override")
    proxy_override = proxy_override_var.get().strip() if proxy_override_var else ""

    configure_global_proxy(enabled=proxy_enabled, override=proxy_override or None, force=False)
    proxies = get_requests_proxies(enabled=proxy_enabled, override=proxy_override or None)
    state["proxies"] = proxies

    provider_name_var = state.get("llm_provider")
    provider_name = provider_name_var.get() if provider_name_var else DEFAULT_PROVIDER
    provider = get_provider(provider_name)

    name_lang = state.get("filename_language").get().lower() if state.get("filename_language") else "english"
    alt_lang = state.get("alttext_language").get().lower() if state.get("alttext_language") else "english"
    detail_level = state.get("name_detail_level").get().lower() if state.get("name_detail_level") else "detailed"
    ocr_enabled = state.get("ocr_enabled").get() if state.get("ocr_enabled") else False
    tesseract_path = state.get("tesseract_path").get() if state.get("tesseract_path") else ""
    ocr_lang = state.get("ocr_language").get() if state.get("ocr_language") else "eng"
    prompt_key = state.get("prompt_key").get() if state.get("prompt_key") else "default"
    prompt_template = get_prompt_template(prompt_key).strip()
    user_context = state.get("context_text").get().strip() if state.get("context_text") else ""

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
