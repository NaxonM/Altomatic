"""OpenAI integration."""

from __future__ import annotations

import json

from openai import OpenAI

from ..models import AVAILABLE_MODELS, DEFAULT_MODEL
from ..prompts import get_prompt_template
from ..ui import append_monitor_colored, update_token_label
from ..utils import extract_text_from_image, image_to_base64


def describe_image(state, image_path: str) -> dict | None:
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

    if "openai_model" in state:
        model_id = state["openai_model"].get()
    else:
        model_id = DEFAULT_MODEL
    if not model_id or model_id not in AVAILABLE_MODELS:
        model_id = DEFAULT_MODEL

    client = OpenAI(api_key=api_key)

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

    try:
        response = client.responses.create(
            model=model_id,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": encoded_image, "detail": vision_detail},
                    ],
                }
            ],
            text={"format": {"type": "json_object"}},
        )

        append_monitor_colored(state, f"[API RAW OUTPUT]\n{response.output_text}", "info")

        if response.usage:
            used = response.usage.total_tokens
            append_monitor_colored(state, f"[TOKEN USAGE] +{used} tokens", "token")
            previous = state["total_tokens"].get()
            state["total_tokens"].set(previous + used)
            update_token_label(state)

        return json.loads(response.output_text)

    except Exception as exc:
        append_monitor_colored(state, f"[API ERROR] {exc}", "error")
        return None
