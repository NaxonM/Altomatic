"""Image utilities for Altomatic."""

from __future__ import annotations

import base64
import os
import random
import string
from datetime import datetime


def generate_short_id(length: int = 4) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def image_to_base64(path: str) -> str:
    extension = os.path.splitext(path)[1].lower().replace(".", "")
    if extension == "jpg":
        extension = "jpeg"
    with open(path, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("utf-8")
    return f"data:image/{extension};base64,{encoded}"


def _timestamp_prefix() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H-%M")


def generate_session_folder_name() -> str:
    return f"session-{_timestamp_prefix()}-{generate_short_id()}"


def generate_output_filename() -> str:
    return f"altomatic-output-{_timestamp_prefix()}-{generate_short_id()}.txt"


def get_image_count_in_folder(folder: str) -> int:
    if not os.path.isdir(folder):
        return 0
    return len([
        file
        for file in os.listdir(folder)
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])


def get_all_images(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, file)
        for file in os.listdir(folder)
        if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]


def get_output_folder(state) -> str:
    preset = state["output_folder_option"].get()
    input_path = state["input_path"].get()
    input_type = state["input_type"].get()

    if preset == "Same as input":
        if input_type == "File":
            return os.path.dirname(input_path)
        return input_path
    if preset == "Desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    if preset == "Pictures":
        return os.path.join(os.path.expanduser("~"), "Pictures")
    if preset == "Custom":
        return state["custom_output_path"].get()
    return os.getcwd()


def slugify(text: str) -> str:
    import re

    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


def extract_text_from_image(image_path: str, tesseract_path: str = "", lang: str = "eng") -> str:
    try:
        from PIL import Image
        import pytesseract

        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as exc:
        return f"⚠️ OCR failed: {exc}"
