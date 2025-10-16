"""LLM integration layer."""

from __future__ import annotations
from typing import Any, Dict, TYPE_CHECKING

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

if TYPE_CHECKING:
    from src.app.viewmodels.footer_viewmodel import FooterViewModel
    from src.app.viewmodels.log_viewmodel import LogViewModel

def get_provider(provider_name: str):
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

def describe_image(state: Dict[str, Any], image_path: str) -> dict | None:
    log_vm: LogViewModel = state["log_vm"]
    footer_vm: FooterViewModel = state["footer_vm"]

    proxy_enabled = bool(state.get("proxy_enabled", True))
    proxy_override = str(state.get("proxy_override", "")).strip()
    configure_global_proxy(enabled=proxy_enabled, override=proxy_override or None, force=False)
    state["proxies"] = get_requests_proxies(enabled=proxy_enabled, override=proxy_override or None)

    provider_name = (state.get("llm_provider") or DEFAULT_PROVIDER) or DEFAULT_PROVIDER

    provider = get_provider(provider_name)

    name_lang = str(state.get("filename_language", "English")).lower()
    alt_lang = str(state.get("alttext_language", "English")).lower()
    detail_level = str(state.get("name_detail_level", "detailed")).lower()
    vision_detail = str(state.get("vision_detail", "auto")).lower()
    ocr_enabled = bool(state.get("ocr_enabled", False))
    tesseract_path = state.get("tesseract_path") or ""
    ocr_lang = state.get("ocr_language") or "eng"
    prompt_key = state.get("prompt_key") or "default"
    prompt_template = get_prompt_template(prompt_key).strip()
    user_context = str(state.get("context_text", "")).strip()

    ocr_text = ""
    if ocr_enabled:
        ocr_result = extract_text_from_image(image_path, tesseract_path, ocr_lang)
        if ocr_result.startswith("⚠️ OCR failed:"):
            log_vm.add_log(ocr_result, "error")
        else:
            log_vm.add_log(f"[OCR RESULT] {ocr_result}", "warn")
            ocr_text = ocr_result

    try:
        processed_image = preprocess_image_for_llm(image_path)
        encoded_image = processed_image.data_url
    except Exception as exc:
        log_vm.add_log(f"[IMAGE PREPROCESS] Failed to compress image: {exc}", "warn")
        encoded_image = image_to_base64(image_path)

    prompt_parts: list[str] = [prompt_template.strip()]
    if user_context:
        prompt_parts.append(f"\nContext from user:\n{user_context}")

    name_words = "1-2" if detail_level == "minimal" else ("up to 3" if detail_level == "normal" else "up to 8")
    prompt_parts.append(
        f"\nOutput requirements:\n- 'name': lowercase, dash-separated, {name_words} words in {name_lang.capitalize()}.\n- 'alt': single clear sentence in {alt_lang.capitalize()}."
    )

    if ocr_text:
        prompt_parts.append(f"\nText detected via OCR:\n{ocr_text}")

    prompt_parts.append("\nRespond ONLY with a valid JSON object containing 'name' and 'alt'.")
    prompt = "\n".join(prompt_parts)

    state["log_vm"] = log_vm
    state["footer_vm"] = footer_vm
    state["vision_detail"] = vision_detail

    return provider.describe_image(encoded_image, prompt, state)
