"""Manage persistent configuration for Altomatic."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from ..models import DEFAULT_MODEL

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".altomatic_config.json")
SECRET_PREFIX = "ALTOMATIC:"


DEFAULT_CONFIG: dict[str, Any] = {
    "custom_output_path": "",
    "output_folder_option": "Same as input",
    "openai_api_key": "",
    "window_geometry": "1133x812",
    "filename_language": "English",
    "alttext_language": "English",
    "name_detail_level": "Detailed",
    "vision_detail": "auto",
    "ocr_enabled": False,
    "tesseract_path": "",
    "ocr_language": "eng",
    "ui_theme": "Default Light",
    "openai_model": DEFAULT_MODEL,
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
