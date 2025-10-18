"""Manage persistent configuration for Altomatic."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from ..models import (
    DEFAULT_MODEL,
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    get_default_model,
)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".altomatic_config.json")
SECRET_PREFIX = "ALTOMATIC:"


DEFAULT_CONFIG: dict[str, Any] = {
    "custom_output_path": "",
    "output_folder_option": "Same as input",
    "llm_provider": DEFAULT_PROVIDER,
    "llm_model": DEFAULT_MODEL,
    "openai_api_key": "",
    "openrouter_api_key": "",
    "proxy_enabled": True,
    "proxy_override": "",
    "window_geometry": "1200x950",
    "filename_language": "English",
    "alttext_language": "English",
    "name_detail_level": "Detailed",
    "vision_detail": "auto",
    "ocr_enabled": False,
    "tesseract_path": "",
    "ocr_language": "eng",
    "ui_theme": "Arctic Light",
    "openai_model": DEFAULT_MODELS["openai"],
    "openrouter_model": get_default_model("openrouter"),
    "prompt_key": "default",
    "context_text": "",
}


def _obfuscate_api_key(plaintext: str) -> str:
    raw = SECRET_PREFIX + plaintext
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def _deobfuscate_api_key(ciphertext: str) -> str:
    try:
        data = base64.b64decode(ciphertext).decode("utf-8")
        if data.startswith(SECRET_PREFIX):
            return data[len(SECRET_PREFIX) :]
        return ""
    except Exception:
        return ""


def load_config() -> dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        if config["openai_api_key"]:
            config["openai_api_key"] = _deobfuscate_api_key(config["openai_api_key"])
        if config.get("openrouter_api_key"):
            config["openrouter_api_key"] = _deobfuscate_api_key(config["openrouter_api_key"])

        provider = config.get("llm_provider") or DEFAULT_PROVIDER
        if provider not in DEFAULT_MODELS:
            provider = DEFAULT_PROVIDER
        config["llm_provider"] = provider

        if "openrouter_provider" in config:
            config.pop("openrouter_provider", None)

        if not config.get("openai_model"):
            config["openai_model"] = DEFAULT_MODELS["openai"]
        if not config.get("openrouter_model"):
            config["openrouter_model"] = get_default_model("openrouter")

        if not config.get("llm_model"):
            config["llm_model"] = config.get(f"{provider}_model", get_default_model(provider))

        if config["llm_model"] not in (
            config.get(f"{provider}_model"),
            get_default_model(provider),
        ):
            config["llm_model"] = config.get(f"{provider}_model", get_default_model(provider))

        legacy_themes = {
            "Light": "Default Light",
            "Dark": "Default Dark",
            "BlueGray": "Default Light",
            "Solarized": "Sakura",
            "Pinky": "Sakura",
        }
        theme_value = config.get("ui_theme")
        if theme_value in legacy_themes:
            config["ui_theme"] = legacy_themes[theme_value]
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(state, geometry: str) -> None:
    data: dict[str, Any] = {}
    for key in DEFAULT_CONFIG:
        if key == "window_geometry":
            data["window_geometry"] = geometry
        elif key == "openai_api_key":
            plain = state["openai_api_key"].get()
            data["openai_api_key"] = _obfuscate_api_key(plain)
        elif key == "openrouter_api_key":
            plain = state["openrouter_api_key"].get()
            data["openrouter_api_key"] = _obfuscate_api_key(plain)
        else:
            data[key] = state[key].get()

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"⚠️ Could not save config: {exc}")


def reset_config() -> None:
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
        except Exception as exc:
            print(f"⚠️ Could not delete config: {exc}")


def open_config_folder() -> None:
    folder = os.path.dirname(CONFIG_FILE)
    if os.name == "nt":
        os.startfile(folder)  # type: ignore[attr-defined]
    elif os.name == "posix":
        import subprocess

        subprocess.call(["xdg-open", folder])
    else:
        print(f"Open config folder not implemented for OS: {os.name}")
